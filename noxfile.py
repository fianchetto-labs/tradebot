from __future__ import annotations

import http.client
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

import nox


nox.options.sessions = ["unit"]
nox.options.default_venv_backend = "venv"

PYTHON = os.environ.get("TRADEBOT_NOX_PYTHON", "3.14")
SERVICE_TEST_ENV_VAR = "TRADEBOT_RUN_SERVICE_TESTS"
LIVE_E2E_TEST_ENV_VAR = "TRADEBOT_RUN_LIVE_E2E_TESTS"
DOCKER_IMAGE = os.environ.get("TRADEBOT_DOCKER_IMAGE", "tradebot:local")
SMOKE_CONTAINER_TTL_SECONDS = 30 * 60
INTEGRATION_STACK_TTL_ENV_VAR = "TRADEBOT_INTEGRATION_STACK_TTL_SECONDS"
DEFAULT_INTEGRATION_STACK_TTL_SECONDS = 30 * 60
REPO_ROOT = Path(__file__).parent
DOCKER_INTEGRATION_COMPOSE_FILE = REPO_ROOT / "deploy" / "docker" / "docker-compose.integration.yml"
UNIT_PYTEST_MARKER_EXPR = "not functional and not contract and not service and not docker and not integration and not live_e2e"
FUNCTIONAL_PYTEST_MARKER_EXPR = "functional and not service and not docker and not integration and not live_e2e"


@dataclass(frozen=True)
class DockerService:
    name: str
    module: str
    container_port: int
    host_port: int


DOCKER_SMOKE_SERVICES = [
    DockerService(
        name="orders",
        module="fianchetto_tradebot.server.orders.serving.orders_rest_service",
        container_port=8080,
        host_port=18080,
    ),
    DockerService(
        name="quotes",
        module="fianchetto_tradebot.server.quotes.serving.quotes_rest_service",
        container_port=8081,
        host_port=18081,
    ),
    DockerService(
        name="moex",
        module="fianchetto_tradebot.server.moex.serving.moex_rest_service",
        container_port=8082,
        host_port=18082,
    ),
]


def _install_project(session: nox.Session) -> None:
    session.install("-e", ".[dev]")


def _run_pytest(session: nox.Session, *args: str) -> None:
    session.run("python", "-m", "pytest", *args)


def _require_env_gate(session: nox.Session, env_var: str, purpose: str) -> None:
    if os.getenv(env_var) != "1":
        session.skip(f"set {env_var}=1 to run {purpose}")


def _require_docker_available(session: nox.Session) -> None:
    if shutil.which("docker") is None:
        session.error("docker is required for this session but was not found on PATH")


def _require_dockerfile(session: nox.Session) -> None:
    if not (REPO_ROOT / "Dockerfile").exists():
        session.error("Dockerfile is required for this session; land FIA-133 before running it")


def _docker_build(session: nox.Session) -> None:
    _require_docker_available(session)
    _require_dockerfile(session)
    session.run(
        "docker",
        "build",
        "--build-arg",
        "PYTHON_VERSION=3.14",
        "-t",
        DOCKER_IMAGE,
        ".",
        external=True,
    )


def _run_docker_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        check=True,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _run_docker_compose(session: nox.Session, *args: str, env: dict[str, str] | None = None) -> None:
    session.run(
        "docker",
        "compose",
        "-f",
        str(DOCKER_INTEGRATION_COMPOSE_FILE),
        *args,
        external=True,
        env=env or {**os.environ, "TRADEBOT_DOCKER_IMAGE": DOCKER_IMAGE},
    )


def _wait_for_health(service: DockerService, timeout_seconds: int = 30) -> None:
    health_url = f"http://127.0.0.1:{service.host_port}/health-check"
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return
        except (
            ConnectionResetError,
            http.client.RemoteDisconnected,
            urllib.error.URLError,
            TimeoutError,
        ) as exc:
            last_error = exc
        time.sleep(1)

    raise RuntimeError(f"{service.name} did not become healthy at {health_url}: {last_error}")


def _container_name(service: DockerService) -> str:
    return f"tradebot-nox-smoke-{service.name}"


def _start_smoke_service(service: DockerService, run_id: str) -> None:
    _run_docker_command(
        "run",
        "-d",
        "--name",
        _container_name(service),
        "--label",
        "fianchetto.tradebot.kind=nox-smoke",
        "--label",
        f"fianchetto.tradebot.run-id={run_id}",
        "--label",
        f"fianchetto.tradebot.ttl-seconds={SMOKE_CONTAINER_TTL_SECONDS}",
        "-e",
        "FIANCHETTO_TRADEBOT_STATE_DIR=/app/deploy/docker/demo-state",
        "-e",
        f"TRADEBOT_HEALTHCHECK_PORT={service.container_port}",
        "-p",
        f"127.0.0.1:{service.host_port}:{service.container_port}",
        DOCKER_IMAGE,
        "python",
        "-m",
        service.module,
    )


def _schedule_smoke_service_cleanup(run_id: str) -> None:
    cleanup_script = (
        "import subprocess, sys, time; "
        "time.sleep(int(sys.argv[1])); "
        "containers = subprocess.run("
        "['docker', 'ps', '-a', '--filter', f'label=fianchetto.tradebot.run-id={sys.argv[2]}', "
        "'--format', '{{.ID}}'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, "
        "text=True, check=False).stdout.splitlines(); "
        "containers and subprocess.run(['docker', 'rm', '-f', *containers], "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)"
    )
    subprocess.Popen(
        [sys.executable, "-c", cleanup_script, str(SMOKE_CONTAINER_TTL_SECONDS), run_id],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _integration_stack_ttl_seconds(session: nox.Session) -> int:
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        return 0

    raw_ttl = os.getenv(INTEGRATION_STACK_TTL_ENV_VAR)
    if raw_ttl is None:
        return DEFAULT_INTEGRATION_STACK_TTL_SECONDS

    try:
        ttl_seconds = int(raw_ttl)
    except ValueError:
        session.error(f"{INTEGRATION_STACK_TTL_ENV_VAR} must be a non-negative integer number of seconds")

    if ttl_seconds < 0:
        session.error(f"{INTEGRATION_STACK_TTL_ENV_VAR} must be a non-negative integer number of seconds")
    return ttl_seconds


def _integration_compose_env(run_id: str, ttl_seconds: int) -> dict[str, str]:
    return {
        **os.environ,
        "TRADEBOT_DOCKER_IMAGE": DOCKER_IMAGE,
        "TRADEBOT_INTEGRATION_RUN_ID": run_id,
        INTEGRATION_STACK_TTL_ENV_VAR: str(ttl_seconds),
    }


def _schedule_integration_stack_cleanup(run_id: str, ttl_seconds: int) -> None:
    cleanup_script = (
        "import subprocess, sys, time; "
        "time.sleep(int(sys.argv[1])); "
        "run_id = sys.argv[2]; "
        "filters = ['--filter', 'label=fianchetto.tradebot.kind=docker-integration', "
        "'--filter', f'label=fianchetto.tradebot.run-id={run_id}']; "
        "containers = subprocess.run(['docker', 'ps', '-a', *filters, '--format', '{{.ID}}'], "
        "stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False).stdout.splitlines(); "
        "containers and subprocess.run(['docker', 'rm', '-f', *containers], "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False); "
        "networks = subprocess.run(['docker', 'network', 'ls', *filters, '--format', '{{.ID}}'], "
        "stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False).stdout.splitlines(); "
        "networks and subprocess.run(['docker', 'network', 'rm', *networks], "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)"
    )
    subprocess.Popen(
        [sys.executable, "-c", cleanup_script, str(ttl_seconds), run_id],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _format_duration(seconds: int) -> str:
    if seconds % 60 == 0:
        minutes = seconds // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"
    unit = "second" if seconds == 1 else "seconds"
    return f"{seconds} {unit}"


def _stop_smoke_service(service: DockerService) -> None:
    subprocess.run(
        ["docker", "rm", "-f", _container_name(service)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


@nox.session(python=PYTHON, venv_backend="venv", download_python="never")
def unit(session: nox.Session) -> None:
    """Run the safe service-free test suite."""
    _install_project(session)
    _run_pytest(session, "-m", UNIT_PYTEST_MARKER_EXPR, "tests")


@nox.session(python=PYTHON, venv_backend="venv", download_python="never")
def functional(session: nox.Session) -> None:
    """Run service-free tests that exercise multiple components in-process."""
    _install_project(session)
    _run_pytest(session, "-m", FUNCTIONAL_PYTEST_MARKER_EXPR, "tests")


@nox.session(python=PYTHON, venv_backend="venv", download_python="never")
def test(session: nox.Session) -> None:
    """Run pytest with optional passthrough args, e.g. nox -s test -- tests/common/test_chain.py."""
    _install_project(session)
    _run_pytest(session, *(session.posargs or ["tests"]))


@nox.session(python=False)
def docker_build(session: nox.Session) -> None:
    """Build the local TradeBot Docker image."""
    _docker_build(session)


@nox.session(python=False)
def docker_smoke(session: nox.Session) -> None:
    """Build the image and verify representative service health checks."""
    _require_env_gate(session, SERVICE_TEST_ENV_VAR, "Docker-backed service smoke tests")
    _docker_build(session)

    for service in DOCKER_SMOKE_SERVICES:
        _stop_smoke_service(service)

    run_id = uuid.uuid4().hex
    started_services: list[DockerService] = []
    try:
        for service in DOCKER_SMOKE_SERVICES:
            _start_smoke_service(service, run_id)
            started_services.append(service)
            _wait_for_health(service)
            session.log("%s service is healthy on port %s", service.name, service.host_port)
    finally:
        if started_services:
            _schedule_smoke_service_cleanup(run_id)
            session.log(
                "Smoke containers will remain available for %s minutes, then be removed.",
                SMOKE_CONTAINER_TTL_SECONDS // 60,
            )


@nox.session(python=PYTHON, venv_backend="venv", download_python="never")
def docker_integration(session: nox.Session) -> None:
    """Build the image, run the simulator-backed Compose stack, and execute Docker tests."""
    _require_env_gate(session, SERVICE_TEST_ENV_VAR, "Docker-backed integration tests")
    _install_project(session)
    _docker_build(session)

    run_id = uuid.uuid4().hex
    ttl_seconds = _integration_stack_ttl_seconds(session)
    compose_env = _integration_compose_env(run_id, ttl_seconds)

    try:
        _run_docker_compose(session, "down", "--volumes", "--remove-orphans", env=compose_env)
        _run_docker_compose(session, "up", "--detach", "--wait", "--remove-orphans", env=compose_env)
        session.run(
            "python",
            "-m",
            "pytest",
            "-m",
            "docker and integration",
            "tests/integration/docker",
            env={
                **os.environ,
                SERVICE_TEST_ENV_VAR: "1",
                "TRADEBOT_TEST_ORDERS_BASE_URL": "http://127.0.0.1:18080",
                "TRADEBOT_TEST_QUOTES_BASE_URL": "http://127.0.0.1:18081",
            },
        )
    except Exception:
        _run_docker_compose(session, "logs", "--no-color", env=compose_env)
        raise
    finally:
        if ttl_seconds:
            _schedule_integration_stack_cleanup(run_id, ttl_seconds)
            session.log(
                "Integration containers will remain available for %s, then be removed. "
                "Set %s=0 to clean up immediately.",
                _format_duration(ttl_seconds),
                INTEGRATION_STACK_TTL_ENV_VAR,
            )
        else:
            _run_docker_compose(session, "down", "--volumes", "--remove-orphans", env=compose_env)


@nox.session(python=False)
def live_e2e(session: nox.Session) -> None:
    """Reserved for paper-account brokerage E2E tests."""
    _require_env_gate(session, LIVE_E2E_TEST_ENV_VAR, "live paper-account E*Trade E2E tests")
    session.error("live E*Trade paper-account tests belong to FIA-153")
