"""
Base Class for Agent
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

class BaseLangGraphAgent(ABC):
    """
    Base Class fro LangGraph Agent
    """

    NODE_NAMES:ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        model: BaseChatModel | ChatOpenAI,
        state_schema: type,
        input_schema: type,
        output_schema: type,
        agent_name: str | None = None
    ) -> None:
        """
        Initialize Base LangGraph Agent

        Args:
            model: BaseChatModel | ChatOpenAI
            state_schema: type
            input_schema: type
            output_schema: type
            agent_name: str | None = None
        """

        self.model = model
        self.state_schema = state_schema
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.agent_name = agent_name
    
    # -----------------------------------------------------------
    # Shoul Implement before using Agent
    # -----------------------------------------------------------
    @abstractmethod
    def _init_nodes(self, graph: StateGraph) -> None:
        """
        Initialize Nodes for LangGraph Agent

        Args:
            graph: StateGraph
        """
        pass

    @abstractmethod
    def _init_edges(self, graph: StateGraph) -> None:
        """
        Initialize Edges for LangGraph Agent

        Args:
            graph: StateGraph
        """
        pass

    # -----------------------------------------------------------
    # Build Graph
    # -----------------------------------------------------------
    def build_graph(self):
        """
        Build Graph for LangGraph Agent
        """

        _graph = StateGraph(
            state_schema=self.state_schema,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
        )

        self._init_nodes(_graph)
        self._init_edges(_graph)

        self.graph = _graph.compile()