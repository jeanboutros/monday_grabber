"""Monday.com API exceptions."""

from .types import (
    ErrorCode,
    ErrorExtensions,
    ErrorLocation,
    MondayAPIResponse,
    MondayError,
)


# Base exceptions


class MondayAPIException(Exception):
    """Base exception for Monday.com API errors.

    :param message: Error message.
    :param response: Parsed API response.
    :param status_code: HTTP status code.
    :param retry_after: Seconds to wait before retry.
    """

    def __init__(
        self,
        message: str,
        *,
        response: MondayAPIResponse | None = None,
        status_code: int | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.message = message
        self.response = response
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)

    def __str__(self) -> str:
        """Format exception as string."""
        msg = self.message
        if self.status_code:
            msg = f"[HTTP {self.status_code}] {msg}"
        if self.retry_after:
            msg = f"{msg} (Retry after {self.retry_after}s)"
        return msg


# 2xx Application errors


class MondayApplicationError(MondayAPIException):
    """Application-level errors (2xx status with error payload)."""

    pass


class APITemporarilyBlockedException(MondayApplicationError):
    """API usage temporarily blocked."""

    pass


class ColumnValueException(MondayApplicationError):
    """Incorrect column value format."""

    pass


class CorrectedValueException(MondayApplicationError):
    """Query type mismatch."""

    pass


class CreateBoardException(MondayApplicationError):
    """Board creation error."""

    pass


class InvalidArgumentException(MondayApplicationError):
    """Invalid query argument."""

    pass


class InvalidBoardIdException(MondayApplicationError):
    """Invalid board ID."""

    pass


class InvalidColumnIdException(MondayApplicationError):
    """Invalid column ID."""

    pass


class InvalidUserIdException(MondayApplicationError):
    """Invalid user ID."""

    pass


class InvalidVersionException(MondayApplicationError):
    """Invalid API version."""

    pass


class ItemNameTooLongException(MondayApplicationError):
    """Item name exceeds character limit."""

    pass


class ItemsLimitationException(MondayApplicationError):
    """Board exceeded 10,000 items limit."""

    pass


class MissingRequiredPermissionsException(MondayApplicationError):
    """OAuth permission scope exceeded."""

    pass


class ParseErrorException(MondayApplicationError):
    """Query string parse error."""

    pass


class ResourceNotFoundException(MondayApplicationError):
    """Resource ID not found."""

    pass


# 4xx Client errors


class MondayClientError(MondayAPIException):
    """Client errors (4xx status codes)."""

    pass


class BadRequestException(MondayClientError):
    """Incorrect query structure (400)."""

    pass


class JsonParseException(MondayClientError):
    """Invalid JSON in request (400)."""

    pass


class UnauthorizedException(MondayClientError):
    """No permission to access data (401)."""

    pass


class IPRestrictedException(MondayClientError):
    """IP address restricted (401)."""

    pass


class UserUnauthorizedException(MondayClientError):
    """User lacks required permission (403)."""

    pass


class UserAccessDeniedException(MondayClientError):
    """User unauthorized for API (403)."""

    pass


class DeleteLastGroupException(MondayClientError):
    """Cannot delete last group on board (409)."""

    pass


class RecordInvalidException(MondayClientError):
    """Board exceeded subscriber limits (422)."""

    pass


class ResourceLockedException(MondayClientError):
    """Resource temporarily locked (423)."""

    pass


class MaxConcurrencyExceededException(MondayClientError):
    """Too many concurrent queries (429)."""

    pass


class RateLimitExceededException(MondayClientError):
    """Exceeded 5,000 requests per minute (429)."""

    pass


class ComplexityBudgetExhaustedException(MondayClientError):
    """Query complexity limit reached (429)."""

    pass


class IPRateLimitExceededException(MondayClientError):
    """IP rate limit reached (429)."""

    pass


# 5xx Server errors


class MondayServerError(MondayAPIException):
    """Server errors (5xx status codes)."""

    pass


class InternalServerErrorException(MondayServerError):
    """Internal server error (500)."""

    pass


# Error code to exception mapping

ERROR_CODE_MAPPING: dict[str, type[MondayAPIException]] = {
    ErrorCode.API_TEMPORARILY_BLOCKED.value: APITemporarilyBlockedException,
    ErrorCode.COLUMN_VALUE_EXCEPTION.value: ColumnValueException,
    ErrorCode.CORRECTED_VALUE_EXCEPTION.value: CorrectedValueException,
    ErrorCode.CREATE_BOARD_EXCEPTION.value: CreateBoardException,
    ErrorCode.INVALID_ARGUMENT_EXCEPTION.value: InvalidArgumentException,
    ErrorCode.INVALID_BOARD_ID_EXCEPTION.value: InvalidBoardIdException,
    ErrorCode.INVALID_COLUMN_ID_EXCEPTION.value: InvalidColumnIdException,
    ErrorCode.INVALID_USER_ID_EXCEPTION.value: InvalidUserIdException,
    ErrorCode.INVALID_VERSION_EXCEPTION.value: InvalidVersionException,
    ErrorCode.ITEM_NAME_TOO_LONG_EXCEPTION.value: ItemNameTooLongException,
    ErrorCode.ITEMS_LIMITATION_EXCEPTION.value: ItemsLimitationException,
    ErrorCode.MISSING_REQUIRED_PERMISSIONS.value: MissingRequiredPermissionsException,
    ErrorCode.RESOURCE_NOT_FOUND_EXCEPTION.value: ResourceNotFoundException,
    ErrorCode.BAD_REQUEST.value: BadRequestException,
    ErrorCode.JSON_PARSE_EXCEPTION.value: JsonParseException,
    ErrorCode.UNAUTHORIZED.value: UnauthorizedException,
    ErrorCode.YOUR_IP_IS_RESTRICTED.value: IPRestrictedException,
    ErrorCode.USER_UNAUTHORIZED_EXCEPTION.value: UserUnauthorizedException,
    ErrorCode.USER_ACCESS_DENIED.value: UserAccessDeniedException,
    ErrorCode.DELETE_LAST_GROUP_EXCEPTION.value: DeleteLastGroupException,
    ErrorCode.RECORD_INVALID_EXCEPTION.value: RecordInvalidException,
    ErrorCode.RESOURCE_LOCKED.value: ResourceLockedException,
    ErrorCode.MAX_CONCURRENCY_EXCEEDED.value: MaxConcurrencyExceededException,
    ErrorCode.RATE_LIMIT_EXCEEDED.value: RateLimitExceededException,
    ErrorCode.COMPLEXITY_BUDGET_EXHAUSTED.value: ComplexityBudgetExhaustedException,
    ErrorCode.IP_RATE_LIMIT_EXCEEDED.value: IPRateLimitExceededException,
    ErrorCode.INTERNAL_SERVER_ERROR.value: InternalServerErrorException,
}

# HTTP status code to exception mapping

STATUS_CODE_MAPPING: dict[int, type[MondayAPIException]] = {
    400: BadRequestException,
    401: UnauthorizedException,
    403: UserUnauthorizedException,
    404: ResourceNotFoundException,
    409: DeleteLastGroupException,
    422: RecordInvalidException,
    423: ResourceLockedException,
    429: RateLimitExceededException,
    500: InternalServerErrorException,
}
