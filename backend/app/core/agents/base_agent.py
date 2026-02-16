"""Base agent class for the multi-agent hospital ecosystem."""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

import anthropic

from app.core.agents.response_optimizer import response_cache, context_filter

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
        # Check cache first
        cached_response = response_cache.get(self.agent_type, message, case_context)
        if cached_response:
            return cached_response

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

        # Cache the response
        response_cache.set(self.agent_type, message, case_context, response)

        return response

    def _respond_with_claude(
        self, message: str, case_context: dict
    ) -> Optional[tuple[str, str]]:
        """Call Claude with extended thinking. Returns (content, thinking) or None."""
        # Get system prompt with filtered knowledge
        system = self.get_system_prompt(case_context)

        # Inject current vitals and ward transcript into system prompt
        # so this agent knows the current state and what others have said
        ward_transcript = case_context.get("ward_transcript", "")
        elapsed = case_context.get("elapsed_minutes", 0)
        if ward_transcript:
            system += (
                f"\n\n=== CURRENT WARD STATUS (Minute {elapsed}) ===\n"
                f"Current vitals: BP {case_context.get('current_bp', 'N/A')}, "
                f"HR {case_context.get('current_hr', 'N/A')}, "
                f"RR {case_context.get('current_rr', 'N/A')}, "
                f"Temp {case_context.get('current_temp', 'N/A')}°C, "
                f"SpO2 {case_context.get('current_spo2', 'N/A')}%\n\n"
                f"Recent ward conversation (what others have said):\n{ward_transcript}\n\n"
                "Use this context to avoid repeating what has already been said. "
                "Build on the conversation naturally — acknowledge what others mentioned if relevant."
            )
        elif elapsed:
            system += (
                f"\n\n=== CURRENT STATUS (Minute {elapsed}) ===\n"
                f"Current vitals: BP {case_context.get('current_bp', 'N/A')}, "
                f"HR {case_context.get('current_hr', 'N/A')}, "
                f"RR {case_context.get('current_rr', 'N/A')}, "
                f"Temp {case_context.get('current_temp', 'N/A')}°C, "
                f"SpO2 {case_context.get('current_spo2', 'N/A')}%"
            )

        # Apply smart context filtering to reduce prompt size
        if self.specialized_knowledge and len(self.specialized_knowledge) > 1000:
            filtered_knowledge = context_filter.filter_knowledge_for_query(
                self.specialized_knowledge,
                message,
                self.agent_type
            )
            # Replace the full knowledge with filtered version in system prompt
            if filtered_knowledge and len(filtered_knowledge) < len(self.specialized_knowledge):
                system = system.replace(self.specialized_knowledge, filtered_knowledge)
                logger.info(f"Filtered knowledge from {len(self.specialized_knowledge)} to {len(filtered_knowledge)} chars")

        # Compress conversation history to reduce token count
        messages = context_filter.compress_conversation_history(
            self.conversation_history.copy(),
            max_messages=8  # Keep only last 8 messages
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4000,
                temperature=1,  # Required when thinking is enabled
                thinking={
                    "type": "adaptive",  # Opus 4.6: model decides when/how much to think
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
