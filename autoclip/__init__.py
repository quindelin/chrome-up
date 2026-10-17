"""autoclip — automatic short-form clip pipeline for POV streams.

Stream (OBS today, Meta glasses next) -> rolling 5-minute buffer -> local signal
analysis -> an *agent* decides what is worth clipping -> ffmpeg cuts, reframes and
captions it -> publishers push it to YouTube / Instagram / X.

Three ways to drive it:
    python -m autoclip run                  # CLI
    python -m autoclip serve                # REST + OpenAPI  (GET /api/autoclip/schema)
    python -m autoclip mcp                  # MCP stdio server for any agent
"""
from __future__ import annotations

from .agents import (AgentContext, ClipDecision, HeuristicAgent, LLMAgent,
                     RemoteAgent, build_agent, register_agent)
from .pipeline import CycleResult, Pipeline, build_pipeline
from .signals import Analysis

__version__ = "0.1.0"
__all__ = [
    "Pipeline", "CycleResult", "build_pipeline",
    "AgentContext", "ClipDecision", "HeuristicAgent", "LLMAgent", "RemoteAgent",
    "build_agent", "register_agent", "Analysis", "__version__",
]
