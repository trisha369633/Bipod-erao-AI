from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.message_check import router as message_check_router
from app.routes.dual_analysis import router as dual_analysis_router
from app.routes.url_analysis import router as url_analysis_router
from app.routes.url_check import router as url_check_router
from app.services.gemini_analysis import load_gemini_service
from app.services.message_analysis import load_message_model
from app.services.url_classification import URLModelLoadError, load_url_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.message_model = load_message_model()
    application.state.gemini_service = load_gemini_service()
    try:
        application.state.url_model = load_url_model()
    except URLModelLoadError as exc:
        logger.exception("URL classification model is unavailable.")
        application.state.url_model = None
        application.state.url_model_load_error = str(exc)
    yield
    if hasattr(application.state, "url_model"):
        del application.state.url_model
    if hasattr(application.state, "url_model_load_error"):
        del application.state.url_model_load_error
    if hasattr(application.state, "gemini_service"):
        del application.state.gemini_service
    del application.state.message_model


app = FastAPI(
    title="Bipod Erao AI API",
    description="Backend API for the Bipod Erao AI website.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(message_check_router)
app.include_router(dual_analysis_router)
app.include_router(url_analysis_router)
app.include_router(url_check_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, exception: RequestValidationError
) -> JSONResponse:
    errors = [
        {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exception.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Return a welcome message for the API."""
    return {"message": "Welcome to Bipod Erao AI API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
