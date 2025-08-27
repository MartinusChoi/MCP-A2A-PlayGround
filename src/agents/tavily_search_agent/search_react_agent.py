"""
LangGraph Agent using Custom Tavily Search MCP Server

version : demo
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore

from typing import ClassVar

from src.agents.base.base_agent import BaseGraphAgent

class SimpleTavilyMCPAgent(BaseGraphAgent):
    NODE_NAMES: ClassVar[dict[str, str]] = {"REACT" : "react_agent"}

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
        is_debug: bool = True,
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