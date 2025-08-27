"""Web Search MCP Server Based Tavliy Web Search"""

from typing import Any

from mcp_servers.tavily_search.tavily_search_client import TavilySearchAPI
from mcp_servers.base_mcp_server import BaseMCPServer

class TavilyMCPServer(BaseMCPServer):
    """
    Tavily Search MCP Server
    """

    def _initialize_clients(self) -> None:
        self.tavily_api = TavilySearchAPI()

    def _register_tools(self) -> None:

        @self.mcp.tool()
        async def search_web(
            query: str,
            max_results: int = 5,
            search_depth: str = "basic",
            topic: str = "general",
            time_range: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
            days: int | None = None,
            include_domains: list[str] | None = None,
            exclude_domains: list[str] | None = None,
        ) -> dict:
            """
            General Web Search Tool

            - Web Search about Topic/Date/Domain using Tavily API
            - result return with standard structured dict
            """

            try : 
                return await self.tavily_api.search(
                    query=query,
                    max_results=max_results,
                    search_depth=search_depth,
                    topic=topic,
                    time_range=time_range,
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                )
            except Exception as error:
                return await self.handle_error(
                    func_name="search_web", error=error, query=query
                )
        
        @self.mcp.tool()
        async def search_news(
            query: str,
            max_results: int = 10,
            time_range: str = "week",
        ) -> dict:
            """
            New Web Search Tool

            - Perform advanced search specialized in 'news' topic
            - result return with standard structured dict
            """
            try:
                return await self.tavily_api.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    topic="news",
                    time_range=time_range,
                )
            except Exception as error:
                return await self.handle_error(
                    func_name="search_news", error=error, query=query
                )

        @self.mcp.tool()
        async def search_finance(
            query: str,
            max_results: int = 10,
            search_depth: str = "advanced",
            time_range: str = "week",
            start_date: str | None = None,
            end_date: str | None = None,
        ) -> dict:
            """
            Finance Domain Web Search

            - Perform advanced search specialized in 'finance' topic
            - result return with standard structured dict
            """
            try:
                return await self.tavily_api.search(
                    query=query,
                    search_depth=search_depth,
                    max_results=max_results,
                    topic="finance",
                    time_range=time_range,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as error:
                return await self.handle_error(
                    func_name="search_finance", error=error, query=query
                )

def create_app() -> Any:
    server = TavilyMCPServer(server_name="Tavily search MCP Server")
    return server.create_app()