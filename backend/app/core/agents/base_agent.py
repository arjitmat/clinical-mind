"""Base agent class for the multi-agent hospital ecosystem."""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all hospital agents."""

    agent_type: str = "base"
    display_name: str = "Agent"

    def __init__(self):
        self.conversation_history: list[dict] = []
        self.specialized_knowledge: str = ""  # Dynamic RAG+Claude expertise
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client: Optional[anthropic.Anthropic] = None
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"{self.display_name} client init failed: {e}")

    def set_specialized_knowledge(self, knowledge: str):
        """Inject dynamically built expertise into this agent."""
        self.specialized_knowledge = knowledge

    @abstractmethod
    def get_system_prompt(self, case_context: dict) -> str:
        """Return the system prompt for this agent given case context."""

    @abstractmethod
    def get_fallback_response(self, message: str, case_context: dict) -> str:
        """Return a fallback response when the API is unavailable."""

    def respond(self, message: str, case_context: dict) -> dict:
        """Generate a response from this agent.

        Returns dict with: agent_type, display_name, content, metadata
        """
        self.conversation_history.append({"role": "user", "content": message})

        content = ""
        thinking = ""

        if self.client:
            result = self._respond_with_claude(message, case_context)
            if result:
                content, thinking = result

        if not content:
            content = self.get_fallback_response(message, case_context)

        self.conversation_history.append({"role": "assistant", "content": content})

        response = {
            "agent_type": self.agent_type,
            "display_name": self.display_name,
            "content": content,
        }
        if thinking:
            response["thinking"] = thinking
        return response

    def _respond_with_claude(
        self, message: str, case_context: dict
    ) -> Optional[tuple[str, str]]:
        """Call Claude with extended thinking. Returns (content, thinking) or None."""
        system = self.get_system_prompt(case_context)
        messages = self.conversation_history.copy()

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4000,
                temperature=1,  # Required to be 1 for adaptive thinking
                thinking={
                    "type": "adaptive",  # Use adaptive thinking for better performance
                },
                system=system,
                messages=messages,
            )

            content = ""
            thinking = ""
            for block in response.content:
                if block.type == "thinking":
                    thinking = block.thinking
                elif block.type == "text":
                    content = block.text.strip()

            return (content, thinking) if content else None
        except Exception as e:
            logger.error(f"{self.display_name} Claude API error: {e}")
            return None

    def reset(self):
        """Reset conversation history for a new case."""
        self.conversation_history = []
