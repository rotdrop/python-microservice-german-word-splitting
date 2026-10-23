"""FastAPI application."""

from fastapi import FastAPI

from .api.routes import router
from .config import get_port, get_socket


def create_app() -> FastAPI:
    app = FastAPI(title="German Compound Splitter Service")
    app.include_router(router)
    return app


app = create_app()

def run() -> None:
    import uvicorn

    socket_path = get_socket()
    if socket_path:
        uvicorn.run(app, uds=socket_path)
    else:
        uvicorn.run(app, host="127.0.0.1", port=get_port())


if __name__ == "__main__":  # pragma: no cover
    run()
