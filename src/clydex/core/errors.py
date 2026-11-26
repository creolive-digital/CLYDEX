"""Safe user-facing errors; raw exceptions never cross the desktop boundary."""
from dataclasses import dataclass


class ClydexError(RuntimeError):
    code = 'operation_failed'


class PermissionDenied(ClydexError):
    code = 'permission_denied'


class Cancelled(ClydexError):
    code = 'cancelled'


class ProviderError(ClydexError):
    code = 'provider_failed'


class SpeechInputError(ClydexError):
    code = 'speech_input_failed'


@dataclass(frozen=True)
class Failure:
    code: str
    message: str


def failure_for(exc: Exception) -> Failure:
    if isinstance(exc, Cancelled):
        return Failure(exc.code, 'Task stopped. Earlier completed changes remain in place.')
    if isinstance(exc, PermissionDenied):
        return Failure(exc.code, 'Permission was denied, canceled or expired. No further action was run.')
    if isinstance(exc, ProviderError):
        return Failure(exc.code, 'The AI provider could not complete the request. Check configuration, '
                       'credentials, model, connection and request limits.')
    if isinstance(exc, SpeechInputError):
        return Failure(exc.code, 'Speech was unclear or unavailable. Check the microphone and repeat.')
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return Failure('invalid_request', 'The request or response was invalid. Check the target and try again.')
    return Failure('operation_failed', 'The operation failed. Some changes may already have completed. '
                   'Check the application before trying again.')
