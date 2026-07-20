import os

import uvicorn

from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    app,
)

HOST_ENV_VAR = "TRADEBOT_ETRADE_SIMULATOR_HOST"
PORT_ENV_VAR = "TRADEBOT_ETRADE_SIMULATOR_PORT"


def main():
    host = os.environ.get(HOST_ENV_VAR, DEFAULT_HOST)
    port = int(os.environ.get(PORT_ENV_VAR, DEFAULT_PORT))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
