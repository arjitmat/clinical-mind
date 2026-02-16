"""Response optimization utilities for faster agent responses.

Key optimizations:
1. Parallel agent processing
2. Smart context filtering based on query type
3. Response caching for common queries
4. Conversation history compression
"""

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any
import logging
import time

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache for agent responses to reduce API calls."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self._cache: dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _make_key(self, agent_type: str, message: str, context: dict) -> str:
        """Create cache key from request parameters."""
        # Normalize message for better cache hits
        normalized_msg = message.lower().strip()
        normalized_msg = re.sub(r'\s+', ' ', normalized_msg)

        # Include key context elements — elapsed_minutes ensures time-dependent responses aren't stale
        elapsed = context.get('elapsed_minutes', 0)
        context_key = f"{context.get('chief_complaint', '')}-{elapsed}"

        key_string = f"{agent_type}:{normalized_msg}:{context_key}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, agent_type: str, message: str, context: dict) -> Optional[dict]:
        """Get cached response if available and not expired."""
        key = self._make_key(agent_type, message, context)

        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.info(f"Cache hit for {agent_type} agent")
                return response
            else:
                # Expired - remove from cache
                del self._cache[key]

        return None

    def set(self, agent_type: str, message: str, context: dict, response: dict):
        """Cache a response."""
        # Implement simple LRU by removing oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        key = self._make_key(agent_type, message, context)
        self._cache[key] = (response, time.time())


class ContextFilter:
    """Smart context filtering to reduce API payload size."""

    @staticmethod
    def filter_knowledge_for_query(specialized_knowledge: str, message: str, agent_type: str) -> str:
        """Filter specialized knowledge to only relevant sections based on query type."""

        if not specialized_knowledge:
            return ""

        msg_lower = message.lower()

        # For simple/common queries, use minimal context
        simple_queries = [
            "vital", "bp", "heart rate", "temperature", "spo2", "oxygen",
            "how are you", "kaise ho", "feeling", "better", "worse"
        ]
        if any(q in msg_lower for q in simple_queries):
            # Return only first 1000 chars for simple queries
            return specialized_knowledge[:1000]

        # For examination queries, focus on physical exam sections
        if any(w in msg_lower for w in ["examine", "check", "look", "palpat", "auscult"]):
            sections = specialized_knowledge.split("===")
            relevant = [s for s in sections if any(
                kw in s.lower() for kw in ["exam", "physical", "finding", "sign"]
            )]
            return "===".join(relevant[:2])[:3000]  # Limit to 3000 chars

        # For history queries, focus on history/timeline sections
        if any(w in msg_lower for w in ["history", "when", "kab", "started", "began", "pehle"]):
            sections = specialized_knowledge.split("===")
            relevant = [s for s in sections if any(
                kw in s.lower() for kw in ["history", "timeline", "background", "onset"]
            )]
            return "===".join(relevant[:2])[:3000]

        # For treatment queries, focus on management sections
        if any(w in msg_lower for w in ["treatment", "medicine", "dawai", "drug", "manage"]):
            sections = specialized_knowledge.split("===")
            relevant = [s for s in sections if any(
                kw in s.lower() for kw in ["treatment", "management", "medication", "drug", "protocol"]
            )]
            return "===".join(relevant[:2])[:3000]

        # For diagnosis/differential queries
        if any(w in msg_lower for w in ["diagnosis", "differential", "what is", "cause", "why"]):
            sections = specialized_knowledge.split("===")
            relevant = [s for s in sections if any(
                kw in s.lower() for kw in ["diagnosis", "differential", "pathophysiology", "cause"]
            )]
            return "===".join(relevant[:2])[:4000]

        # For investigation queries
        if any(w in msg_lower for w in ["test", "investigation", "lab", "result", "report"]):
            sections = specialized_knowledge.split("===")
            relevant = [s for s in sections if any(
                kw in s.lower() for kw in ["investigation", "lab", "test", "result", "finding"]
            )]
            return "===".join(relevant[:2])[:3000]

        # Default: return first 5000 chars for general queries
        return specialized_knowledge[:5000]

    @staticmethod
    def compress_conversation_history(history: list[dict], max_messages: int = 10) -> list[dict]:
        """Keep only recent messages, summarizing older ones if needed."""

        if len(history) <= max_messages:
            return history

        # Keep last N messages in full
        recent = history[-max_messages:]

        # Add a summary message for older messages if there are many
        if len(history) > max_messages + 5:
            older_count = len(history) - max_messages
            summary_msg = {
                "role": "user",
                "content": f"[Context: {older_count} earlier messages omitted. Patient has been discussing symptoms and undergoing examination. Continue from here.]"
            }
            return [summary_msg] + recent

        return recent


class ParallelAgentProcessor:
    """Process multiple agent responses in parallel."""

    @staticmethod
    def process_agents_parallel(agents_to_process: list[tuple], max_workers: int = 3) -> list[dict]:
        """Process multiple agents in parallel.

        Args:
            agents_to_process: List of tuples (agent, message, context)
            max_workers: Maximum parallel workers (3 is optimal for API rate limits)

        Returns:
            List of agent responses
        """

        if not agents_to_process:
            return []

        start_time = time.time()
        responses = []

        with ThreadPoolExecutor(max_workers=min(max_workers, len(agents_to_process))) as executor:
            # Submit all tasks
            future_to_agent = {
                executor.submit(agent.respond, message, context): (agent, idx)
                for idx, (agent, message, context) in enumerate(agents_to_process)
            }

            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent, idx = future_to_agent[future]
                try:
                    response = future.result(timeout=10)  # 10 second timeout per agent
                    responses.append((idx, response))
                    logger.info(f"Completed response from {agent.display_name}")
                except Exception as e:
                    logger.error(f"Failed to get response from {agent.display_name}: {e}")
                    # Use fallback response
                    fallback = {
                        "agent_type": agent.agent_type,
                        "display_name": agent.display_name,
                        "content": agent.get_fallback_response("", {}),
                    }
                    responses.append((idx, fallback))

        # Sort by original order
        responses.sort(key=lambda x: x[0])
        results = [r[1] for r in responses]

        elapsed = time.time() - start_time
        logger.info(f"Processed {len(results)} agents in parallel in {elapsed:.2f}s")

        return results


# Singleton instances
response_cache = ResponseCache(max_size=200, ttl_seconds=600)  # 10 minute TTL
context_filter = ContextFilter()
parallel_processor = ParallelAgentProcessor()