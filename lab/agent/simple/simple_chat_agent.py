"""
Simple Chat Agent
"""

from agent.base.base_agent import BaseLangGraphAgent

from typing import ClassVar, TypedDict
from typing_extensions import Annotated

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from langgraph.graph import StateGraph, START, END, add_messages

# -----------------------------------------------------------
# Schema
# -----------------------------------------------------------
class InputSchema(TypedDict):
    """
    Input Schema for Simple LangGraph Chat Agent
    """

    query: Annotated[str, "User Query"]

class OutputSchema(TypedDict):
    """
    Output Schema for Simple LangGraph Chat Agent
    """

    generation: Annotated[str, "Generated Response"]

class StateSchema(InputSchema, OutputSchema):
    """
    State Schema for Simple LangGraph Chat Agent
    """
    messages: Annotated[list[BaseMessage], add_messages]


# -----------------------------------------------------------
# Simple LangGraph Chat Agent
# -----------------------------------------------------------
class SimpleLangGraphChatAgent(BaseLangGraphAgent):
    """
    Simple Chat Agent with LangGraph
    """

    NODE_NAMES:ClassVar[dict[str, str]] = {
        "GENERATE" : "generate",
    }

    def __init__(
        self,
        model: BaseChatModel | ChatOpenAI,
        state_schema: type,
        input_schema: type,
        output_schema: type,
        agent_name: str | None = None,
    ) -> None:
        """
        Initialize Simple LangGraph Chat Agent
        """

        super().__init__(
            model=model,
            state_schema=state_schema,
            input_schema=input_schema,
            output_schema=output_schema,
            agent_name=agent_name,
        )

    def _init_nodes(self, graph: StateGraph) -> None:
        """
        Initialize Nodes for Simple LangGraph Chat Agent
        """

        graph.add_node(self.NODE_NAMES["GENERATE"], self._generate_node)
    
    def _init_edges(self, graph: StateGraph) -> None:
        """
        Initialize Edges for Simple LangGraph Chat Agent
        """

        graph.add_edge(START, self.NODE_NAMES["GENERATE"])
        graph.add_edge(self.NODE_NAMES["GENERATE"], END)

    
    # -----------------------------------------------------------
    # Node Functions
    # -----------------------------------------------------------
    def _generate_node(self, state: dict) -> dict:
        """
        Generate Node for Simple LangGraph Chat Agent
        """

        human_message = HumanMessage(content=state["query"])
        ai_message = self.model.invoke([human_message])

        return {
            "query" : state["query"],
            "generation" : ai_message.content,
            "messages" : [human_message, ai_message]
        }