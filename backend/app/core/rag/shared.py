"""Shared singleton instances for the application."""

from app.core.rag.generator import CaseGenerator

# Create a single shared instance of CaseGenerator
# This ensures both cases.py and agents.py use the same instance
# and can share the active_cases dictionary
case_generator = CaseGenerator()