import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import DomainError

logger = logging.getLogger(__name__)


def handle_exception(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=exc.status_code,
        )
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled error")
        return Response(
            {"error": {"code": "internal_error", "message": "Internal server error."}},
            status=500,
        )
    return response
