from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import nox


nox.options.sessions = ["unit"]
nox.options.default_venv_backend = "venv"

PYTHON = os.environ.get("TRADEBOT_NOX_PYTHON", "3.14")
SERVICE_TEST_ENV_VAR = "TRADEBOT_RUN_SERVICE_TESTS"
LIVE_E2E_TEST_ENV_VAR = "TRADEBOT_RUN_LIVE_E2E_TESTS"
DOCKER_IMAGE = os.environ.get("TRADEBOT_DOCKER_IMAGE", "tradebot:local")
REPO_ROOT = Path(__file__).parent
SAFE_PYTEST_MARKER_EXPR = "not service and not docker and not integration and not live_e2e"


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


def _wait_for_health(service: DockerService, timeout_seconds: int = 30) -> None:
    health_url = f"http://127.0.0.1:{service.host_port}/health-check"
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(1)

    raise RuntimeError(f"{service.name} did not become healthy at {health_url}: {last_error}")


def _container_name(service: DockerService) -> str:
    return f"tradebot-nox-smoke-{service.name}"


def _start_smoke_service(service: DockerService) -> None:
    _run_docker_command(
        "run",
        "-d",
        "--rm",
        "--name",
        _container_name(service),
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
    _run_pytest(session, "-m", SAFE_PYTEST_MARKER_EXPR, "tests")


@nox.session(python=PYTHON, venv_backend="venv", download_python="never")
def functional(session: nox.Session) -> None:
    """Run in-process tests until FIA-151 splits functional markers explicitly."""
    _install_project(session)
    session.log("Functional tests are not separately classified yet; running the safe suite.")
    _run_pytest(session, "-m", SAFE_PYTEST_MARKER_EXPR, "tests")


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

    started_services: list[DockerService] = []
    try:
        for service in DOCKER_SMOKE_SERVICES:
            _start_smoke_service(service)
            started_services.append(service)
            _wait_for_health(service)
            session.log("%s service is healthy on port %s", service.name, service.host_port)
    finally:
        for service in reversed(started_services):
            _stop_smoke_service(service)


@nox.session(python=False)
def docker_integration(session: nox.Session) -> None:
    """Reserved for Docker Compose/service-boundary tests."""
    _require_env_gate(session, SERVICE_TEST_ENV_VAR, "Docker-backed integration tests")
    session.error("Docker integration orchestration belongs to FIA-136/FIA-149/FIA-152")


@nox.session(python=False)
def live_e2e(session: nox.Session) -> None:
    """Reserved for paper-account brokerage E2E tests."""
    _require_env_gate(session, LIVE_E2E_TEST_ENV_VAR, "live paper-account E*Trade E2E tests")
    session.error("live E*Trade paper-account tests belong to FIA-153")
