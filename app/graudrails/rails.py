import logfire
from langchain_groq import ChatGroq
from nemoguardrails import LLMRails, RailsConfig

from app.config import settings
from app.graudrails.colang_rules import (
    COLANG_CONTENT,
    YAML_CONTENT,
    RAIL_INDICATORS,
)


_rails: LLMRails | None = None


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.

    Uses llama-3.1-8b-instant for fast intent classification at the gate,
    while the heavier model is reserved for the RAG pipeline.
    """
    global _rails

    guard_llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT,
    )

    _rails = LLMRails(
        config=config,
        llm=guard_llm,
    )

    logfire.info(
        "🛡️ NeMo Guardrails initialised (llama-3.1-8b-instant)."
    )


def guard(message: str) -> tuple[bool, str | None]:
    """
    Run a user message through the NeMo rails gate.

    Returns:
        (True, rail_response):
            A rail fired. Return the rail response immediately
            and skip the RAG pipeline.

        (False, None):
            Message is clean. Proceed to LangGraph/RAG.
    """

    if _rails is None:
        logfire.warning(
            "⚠️ Guardrails not initialised — skipping gate."
        )
        return False, None

    with logfire.span("🛡️ Guardrails Check"):
        result = _rails.generate(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ]
        )

        content = (
            result.get("content", "")
            if isinstance(result, dict)
            else str(result)
        )

        fired = any(
            indicator.lower() in content.lower()
            for indicator in RAIL_INDICATORS
        )

        if fired:
            logfire.info(
                f"🛡️ Guardrails fired | query='{message[:80]}'"
            )
            return True, content

        logfire.info("✅ Guardrails passed.")
        return False, None