"""Errors as application/problem+json with a stable code and a message in the user's language (API 1)."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.i18n import MESSAGES, language_from_header, message

log = logging.getLogger("internsync")


class ApiError(Exception):
    def __init__(self, status: int, code: str, errors: list[dict] | None = None, **extra):
        super().__init__(code)
        self.status = status
        self.code = code
        self.errors = errors or []
        self.extra = extra


def bad(code: str, **extra) -> ApiError:
    return ApiError(422, code, **extra)


def conflict(code: str, **extra) -> ApiError:
    return ApiError(409, code, **extra)


def forbidden(code: str = "FORBIDDEN") -> ApiError:
    return ApiError(403, code)


def not_found() -> ApiError:
    return ApiError(404, "NOT_FOUND")


def field_error(field: str, code: str) -> ApiError:
    return ApiError(422, code, errors=[{"field": field, "code": code}])


def request_language(request: Request) -> str:
    """The signed-in user's language (set by authentication on request.state), else Accept-Language.
    Sync dependencies run in worker threads, so a context variable set there does not reach the handlers."""
    return getattr(request.state, "lang", None) or language_from_header(request.headers.get("accept-language"))


def problem(status: int, code: str, errors: list | None = None, lang: str = "ar", **extra) -> JSONResponse:
    errors = [{**e, "message": message(e["code"], lang)} if e.get("code") in MESSAGES else e for e in errors or []]
    body = {"type": "about:blank", "title": message(code, "en"), "status": status, "code": code,
            "detail": message(code, lang), "errors": errors}
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return problem(exc.status, exc.code, exc.errors, request_language(request), **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = []
        for e in exc.errors():
            loc = [str(x) for x in e.get("loc", []) if x not in ("body", "query", "path", "form")]
            errors.append({"field": ".".join(loc), "code": e.get("type", "invalid"), "message": e.get("msg", "")})
        return problem(422, "VALIDATION_ERROR", errors, request_language(request))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "VALIDATION_ERROR")
        return problem(exc.status_code, code, lang=request_language(request))

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        log.exception("unhandled error", exc_info=exc)
        return problem(500, "INTERNAL_ERROR", lang=request_language(request))
