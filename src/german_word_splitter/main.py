"""FastAPI application."""

from fastapi import FastAPI

from .api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="German Compound Splitter Service")
    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    from .config import get_port

    uvicorn.run(app, host="127.0.0.1", port=get_port())
