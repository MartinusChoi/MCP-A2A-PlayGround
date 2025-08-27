"""
LangGraph Agent using Custom Tavily Search MCP Server

version : demo
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore
from langchain_core.messages import BaseMessage

from typing import ClassVar, TypedDict
from typing import Annotated

from src.agents.base.base_agent import BaseGraphAgent

# -----------------------------------------------------------
# Schemas
# -----------------------------------------------------------
class InputSchema(TypedDict):
    query: Annotated[str, "User Query"]

class OutputState(TypedDict):
    answer: Annotated[str, "Answer from the agent"]

class StateSchema(InputSchema, OutputState):
    messages: Annotated[list[BaseMessage], add_messages]

# -----------------------------------------------------------
# Simple Tavily Search Agent
# -----------------------------------------------------------
class SimpleTavilyMCPAgent(BaseGraphAgent):
    """
    Simple Tavily Search Agent using LangGraph.
    """

    # -----------------------------------------------------------
    # Class Variables
    # -----------------------------------------------------------
    NODE_NAMES: ClassVar[dict[str, str]] = {"REACT" : "react_agent"}

    # -----------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------
    def __init__(
        self,
        model: BaseChatModel | None = None,
        state_schema: type | None = None,
        config_schema: type | None = None,
        input_state: type | None = None,
        output_state: type | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str | None = None,
    ):
        """
        Initialize Simple Tavily Search Agent.
        """
        super().__init__(
            model=model,
            model=model,
            state_schema=state_schema,
            config_schema=config_schema,
            input_state=input_state,
            output_state=output_state,
            checkpointer=checkpointer,
            store=store,
            max_retry_attempts=max_retry_attempts,
            agent_name=agent_name,
            auto_build=False,
        )

        self.llm = model
        self.mcp_server_url = "http://localhost:3001/mcp/"
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
    
    # -----------------------------------------------------------
    # Class Methods
    # -----------------------------------------------------------
    @classmethod
    async def create(
        cls,
        model: BaseChatModel | None = None,
        state_schema: type | None = None,
        config_schema: type | None = None,
        input_state: type | None = None,
        output_state: type | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        store: BaseStore | None = None,
        max_retry_attempts: int = 2,
        agent_name: str | None = None,
    ) -> "SimpleTavilyMCPAgent":
        """
        비동기 초기화 팩토리. 
        MCP 도구를 await로 로딩한 뒤 그래프를 빌드한다.
        """
        self = cls(
            model=model,
            state_schema=state_schema,
            config_schema=config_schema,
            input_state=input_state,
            output_state=output_state,
            checkpointer=checkpointer,
            store=store,
            max_retry_attempts=max_retry_attempts,
            agent_name=agent_name,
        )
        self.tools = await self.mcp_client.get_tools() # NOTE: Key point!
        self.build_graph() # NOTE: 여기서는 자식 그래프에서 호출함.
        return self
    
    # -----------------------------------------------------------
    # Override Methods
    # -----------------------------------------------------------
    def _init_nodes(self, graph: StateGraph):
        """
        Initialize Nodes for Simple Tavily Search Agent.
        """
        graph.add_node(self.NODE_NAMES["REACT"], self.get_react_agent())
    
    def _init_edges(self, graph: StateGraph):
        """
        Initialize Edges for Simple Tavily Search Agent.
        """
        graph.add_edge(START, self.NODE_NAMES["REACT"])
        graph.add_edge(self.NODE_NAMES["REACT"], END)
        

    # -----------------------------------------------------------
    # Node Methods
    # -----------------------------------------------------------
    def get_react_agent(self):
        """
        Get React Agent for Simple Tavily Search Agent.
        """
        return create_react_agent(
            llm=self.llm,
            tools=self.tools or [],
            prompt="""
            당신은 웹 검색 도구를 가지고 있는 검색 전문가입니다.
            필요 시 가진 도구를 사용해 답변하세요.
            - search_web(query): 일반 웹 검색
            - serach_news(query): 뉴스 검색
            결과가 부족하면 모른다고 답하면 됩니다. 도구의 결과를 활용해 출처를 꼭 제공하세요.
            """
        )