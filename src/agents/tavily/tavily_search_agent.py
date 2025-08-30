"""
Tavily Search Agent
"""
import os
from uuid import uuid4
from langgraph.graph.state import Runnable
from pydantic.v1.networks import MultiHostDsn
from src.agents.base.base_agent import BaseLangGraphAgent

from typing import TypedDict, ClassVar, Any
from typing_extensions import Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    BaseMessage,
)
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# -----------------------------------------------------------
# Schema
# -----------------------------------------------------------
class InputSchema(TypedDict):
    """
    Input Schema for Tavily Search Agent
    """

    messages: Annotated[list[BaseMessage], add_messages]

class OutputSchema(TypedDict):
    """
    Output Schema for Tavily Search Agent
    """

    response: Annotated[str, "Answer of Agent based on Tavily Search results"]

class StateSchema(InputSchema, OutputSchema):
    """
    Graph State Schema for Tavily Search Agent
    """

    pass

# -----------------------------------------------------------
# Tavily Search Agent
# -----------------------------------------------------------
class TavilySearchAgent(BaseLangGraphAgent):
    """
    Tavily Search Agent
    """

    NODE_NAMES:ClassVar[dict[str, str]] = {
        "SEARCH_AGENT" : "search_agent",
    }

    def __init__(
        self,
        model: ChatOpenAI | None = None,
        state_schema: StateSchema | None = None,
        input_schema: InputSchema | None = None,
        output_schema: OutputSchema | None = None,
        agent_name: str | None = None,
        auto_build: bool = False,
    ):
        """
        Initialize Tavily Search Agent
        """

        super().__init__(
            model=model,
            state_schema=state_schema,
            input_schema=input_schema,
            output_schema=output_schema,
            agent_name=agent_name,
            auto_build=auto_build,
        )

        self.model = model
        self.mcp_server_url = "http://localhost:3000/mcp/"
        self.mcp_server_config = {
            "transport" : "streamable_http"
        }
        self.mcp_client = MultiServerMCPClient(
            {
                "tavily-search" : {
                    "url" : self.mcp_server_url,
                    **self.mcp_server_config
                }
            }
        )
        self.tools = []
    
    # -----------------------------------------------------------
    # Implement Graph Nodes and Edges
    # -----------------------------------------------------------
    def _init_nodes(self, graph: StateGraph) -> None:
        """
        Initialize Nodes for Tavily Search Agent
        """

        graph.add_node(self.get_node_name("SEARCH_AGENT"), self.get_react_agent())
    
    def _init_edges(self, graph: StateGraph) -> None:
        graph.add_edge(START, self.get_node_name("SEARCH_AGENT"))
        graph.add_edge(self.get_node_name("SEARCH_AGENT"), END)
    
    # -----------------------------------------------------------
    # create agent application
    # -----------------------------------------------------------
    @classmethod
    async def create(
        cls,
        model: ChatOpenAI | None = None,
        state_schema: StateSchema | None = None,
        input_schema: InputSchema | None = None,
        output_schema: OutputSchema | None = None,
        agent_name: str | None = None,
        enable_langsmith_tracing: bool = False,
    ) -> "TavilySearchAgent":
        """
        Async Initialize Tavily Search Agent

        Graph will be build after load mcp tools.
        """

        self = cls(
            model=model or ChatOpenAI(model="gpt-4o-mini", temperature=0),
            state_schema=state_schema or StateSchema,
            input_schema=input_schema or InputSchema,
            output_schema=output_schema or OutputSchema,
            agent_name=agent_name or cls.__name__,
        )
        
        self.tools = await self.mcp_client.get_tools()
        self.build_graph() # build sub graph

        return self

    # -----------------------------------------------------------
    # Node Methods
    # -----------------------------------------------------------
    def get_react_agent(self):
        prompt = """
        당신은 웹 도구를 가진 검색 전문가입니다.
        
        임무 : 사용자의 질문에 실시간 정보를 반영한 답변을 제공하기 위해 검색 도구로 검색을 수행하고, 이를 기반으로 답변하는 것.
        
        도구: 
            - search_web : 기본 웹 검색 도구
            - search_news : 뉴스 검색 도구
            - search_finance : 금융 도메인 검색 도구
        
        지시사항:
            - 사용자의 질문에 답변하기 위해 적절한 검색어를 만들어 검색을 수행하세요.
            - 수집된 결과가 부족하다면 "모른다"고 답하세요.
            - 수집된 결과에만 기반하여 답변을 제공하세요.
            - 답변에 반드시 출처를 포함하세요.
        """
        return create_react_agent(
            self.model,
            tools=self.tools,
            prompt=prompt
        )
    
# -----------------------------------------------------------
# run config utility (include langsmith tracing)
# -----------------------------------------------------------
def create_run_config(
        run_name: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        enable_langsmith_tracing: bool = False
    ) -> RunnableConfig:
    """
    Create RunnableConfig for LangSmith Tracing
    """
    if enable_langsmith_tracing:
        config = RunnableConfig(
            configurable={"run_id": uuid4()},
            run_name=run_name or f"DefaultRunName",
            run_id=uuid4(),
            tags=tags or ["tavily-search"],
            metadata=metadata or {
                "agent_type" : "tavily-search",
                "version" : "0.0.1",
                "environment" : os.getenv("ENV", "development")
            }
        )
    else:
        config = RunnableConfig(
            configurable={"run_id": uuid4()}
        )

    return config