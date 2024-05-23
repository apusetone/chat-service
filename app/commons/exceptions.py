import logging

from asyncpg.exceptions import PostgresError
from fastapi import FastAPI, Request
from fastapi.exceptions import FastAPIError, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core._pydantic_core import ValidationError

logging.basicConfig(level=logging.INFO)


def register_exception_handlers(app: FastAPI):
    # Handler for RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def bad_request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        # Log the validation errors with traceback
        logging.warning("Validation error", exc_info=exc)
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "BAD_REQUEST",
                "message": "Request parameters validation failed",
                "detail": [],
            },
        )

    # Handler for pydantic_core validation errors
    @app.exception_handler(ValidationError)
    async def pydantic_core_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        # Log the validation error with traceback
        logging.warning("A validation error occurred", exc_info=exc)
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "BAD_REQUEST",
                "message": "Request parameters validation failed",
                "detail": [],
            },
        )

    # Handler for PostgresError
    @app.exception_handler(PostgresError)
    async def asyncpg_exception_handler(request: Request, exc: PostgresError):
        # Log the PostgresError error with traceback
        logging.error(
            "An internal server error occurred (Postgres error)", exc_info=exc
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "detail": [],
            },
        )

    # Handler for FastAPIError
    @app.exception_handler(FastAPIError)
    async def fastapi_internal_server_error_handler(
        request: Request, exc: FastAPIError
    ):
        # Log the FastAPI error with traceback
        logging.error("An internal server error occurred (FastAPI error)", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "detail": [],
            },
        )

    # General exception handler for all other exceptions
    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        # Log the exception details with traceback
        logging.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "detail": [],
            },
        )
