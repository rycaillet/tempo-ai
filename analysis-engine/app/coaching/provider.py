from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)


class CoachingProviderError(RuntimeError):
    """
    Structured provider failure safe for application-level handling.

    The message remains generic. Diagnostic fields may be logged by a
    trusted server process but should not be exposed directly to users.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "provider_error",
        request_id: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.request_id = request_id
        self.retryable = retryable


@runtime_checkable
class CoachingProvider(Protocol):
    """
    Provider-independent contract for generating coaching language.

    Implementations may use deterministic logic, an external LLM,
    or another future coaching system. All providers consume the same
    validated CoachContext and return the same CoachResponse model.
    """

    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        """
        Generate a structured coaching response from validated context.
        """
        ...