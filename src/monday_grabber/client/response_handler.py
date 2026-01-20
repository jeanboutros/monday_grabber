"""Response handling and error parsing for Monday.com API."""

import requests

from monday_grabber.core.exceptions import (
    ERROR_CODE_MAPPING,
    STATUS_CODE_MAPPING,
    MondayAPIException,
    MondayAPIResponse,
    MondayApplicationError,
    MondayServerError,
    ParseErrorException,
)


class ResponseHandler:
    """Handles parsing and error detection for API responses."""

    # Error codes that indicate retryable errors
    RETRYABLE_CODES: frozenset[str] = frozenset(
        {
            "API_TEMPORARILY_BLOCKED",
            "maxConcurrencyExceeded",
            "RateLimitExceeded",
            "COMPLEXITY_BUDGET_EXHAUSTED",
            "IP_RATE_LIMIT_EXCEEDED",
            "ResourceLocked",
            "InternalServerError",
        }
    )

    @classmethod
    def parse(cls, *, response: requests.Response) -> MondayAPIResponse:
        """Parse HTTP response into MondayAPIResponse.

        :param response: HTTP response object.
        :returns: Parsed API response.
        """
        retry_after = cls._extract_retry_after(response=response)

        try:
            data = response.json()
        except ValueError:
            data = {
                "data": None,
                "errors": [
                    {
                        "message": f"Invalid JSON: {response.text[:200]}",
                        "locations": [],
                        "path": [],
                        "extensions": {
                            "code": "JsonParseException",
                            "error_data": {},
                            "status_code": response.status_code,
                        },
                    }
                ],
            }

        return MondayAPIResponse.from_dict(data, retry_after=retry_after)

    @classmethod
    def handle(
        cls,
        *,
        response: requests.Response,
        raise_on_error: bool = True,
    ) -> MondayAPIResponse:
        """Parse response and raise exceptions on errors.

        :param response: HTTP response object.
        :param raise_on_error: Whether to raise on errors.
        :returns: Parsed API response.
        :raises MondayAPIException: On API errors if raise_on_error is True.
        """
        parsed = cls.parse(response=response)

        if raise_on_error:
            if response.status_code != 200:
                cls._raise_transport_error(
                    status_code=response.status_code,
                    response=parsed,
                )

            if parsed.has_errors():
                cls._raise_application_error(response=parsed)

        return parsed

    @classmethod
    def is_retryable(cls, *, exception: MondayAPIException) -> bool:
        """Check if error is retryable.

        :param exception: Exception to check.
        :returns: True if retryable.
        """
        if isinstance(exception, MondayServerError):
            return True

        if exception.response:
            error_codes = exception.response.get_error_codes()
            return any(code in cls.RETRYABLE_CODES for code in error_codes)

        return False

    @classmethod
    def get_retry_delay(cls, *, exception: MondayAPIException) -> int | None:
        """Get recommended retry delay.

        :param exception: Exception with retry info.
        :returns: Seconds to wait, or None if not specified.
        """
        return exception.retry_after

    @classmethod
    def _extract_retry_after(cls, *, response: requests.Response) -> int | None:
        """Extract Retry-After header value.

        :param response: HTTP response.
        :returns: Retry delay in seconds, or None.
        """
        if "Retry-After" in response.headers:
            try:
                return int(response.headers["Retry-After"])
            except (ValueError, TypeError):
                pass
        return None

    @classmethod
    def _raise_transport_error(
        cls,
        *,
        status_code: int,
        response: MondayAPIResponse,
    ) -> None:
        """Raise exception for HTTP transport errors.

        :param status_code: HTTP status code.
        :param response: Parsed API response.
        :raises MondayAPIException: Always raises.
        """
        message = (
            response.errors[0].message
            if response.errors
            else f"HTTP {status_code} error"
        )

        exception_class = STATUS_CODE_MAPPING.get(status_code, MondayAPIException)

        raise exception_class(
            message,
            response=response,
            status_code=status_code,
            retry_after=response.retry_after,
        )

    @classmethod
    def _raise_application_error(cls, *, response: MondayAPIResponse) -> None:
        """Raise exception for application-level errors.

        :param response: Parsed API response with errors.
        :raises MondayAPIException: Always raises.
        """
        first_error = response.errors[0]
        error_code = first_error.extensions.code
        message = first_error.message

        if "parse error" in message.lower():
            exception_class = ParseErrorException
        else:
            exception_class = ERROR_CODE_MAPPING.get(
                error_code,
                MondayApplicationError,
            )

        raise exception_class(
            message,
            response=response,
            status_code=first_error.extensions.status_code,
            retry_after=response.retry_after,
        )
