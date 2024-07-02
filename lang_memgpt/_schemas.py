from __future__ import annotations

from typing import List

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated, TypedDict


class GraphConfig(TypedDict):
    model: str | None
    """The model to use for the memory assistant."""
    thread_id: str
    """The thread ID of the conversation."""
    user_id: str
    """The ID of the user to remember in the conversation."""


# Define the schema for the state maintained throughout the conversation
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    """The messages in the conversation."""
    core_memories: List[str]
    """The core memories associated with the user."""
    recall_memories: List[str]
    """The recall memories retrieved for the current context."""


__all__ = [
    "State",
    "GraphConfig",
]
