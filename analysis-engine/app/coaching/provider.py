from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)


class CoachingProviderError(RuntimeError):
    """
    Base exception raised when a coaching provider cannot generate
    a usable response.
    """


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