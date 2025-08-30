"""
Web Search Server based on Tavily API.
"""

from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_servers.tavily_search.client import TavilySearchClient

from typing import Any, Literal, Sequence, Union, cast

class TavilyMCPServer(BaseMCPServer):
    """
    Web Search MCP Server based on Tavily API.
    """

    def _initialize_clients(self) -> None:
        self.tavily_client = TavilySearchClient()
    
    def _register_tools(self) -> None:
        @self.mcp.tool()
        async def search_web(
            query: str,
            search_depth: Literal["basic", "advanced"] = "basic",
            topic: Literal["general", "news", "finance" ] = "general",
            time_range: Literal["day", "week", "month", "year"] = None,
            start_date: str = None,
            end_date: str = None,
            days: int = None,
            max_results: int = 5,
            include_domains: Sequence[str] = None,
            exclude_domains: Sequence[str] = None,
            include_answer: Union[bool, Literal["basic", "advanced"]] = None,
            include_raw_content: Union[bool, Literal["markdown", "text"]] = None,
            include_images: bool = None,
            timeout: int = 60,
            country: str = None,
        ):
            """
            Basic Search Web with Tavily API.

            Args:
                query : Search Query
                search_depth : Search Depth (basic, advanced)
                topic : Search Topic (general, news, finance)
                time_range : Search Time Range (day, week, month, year)
                start_date : Start Date (YYYY-MM-DD)
                end_date : End Date (YYYY-MM-DD)
                days : Search Days (1-30)
                max_results : Maximum Results (1-100)
                include_domains : Include Domains (List of Strings)
                exclude_domains : Exclude Domains (List of Strings)
                include_answer : Include Answer (True, False)
                include_raw_content : Include Raw Content (True, False)
                include_images : Include Images (True, False)
                timeout : Timeout (seconds)
                country : Country (ISO 3166-1 alpha-2)
            """
            try:
                self.logger.info(f"Calling 'search_web' tool with query: '{query}'")
                result = await self.tavily_client.search(
                    query=query,
                    search_depth=search_depth,
                    topic=topic,
                    time_range=time_range,
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                    max_results=max_results,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content,
                    include_images=include_images,
                    timeout=timeout,
                    country=country,
                )
                self.logger.info(f"Search web results: {len(result)}")
                return result
            except Exception as error:
                self.logger.error(f"Error in 'search_web': {error}")
                return self.create_error_response(
                    error=error, 
                    query=query, 
                    func_name="search_web"
                )
        
        @self.mcp.tool()
        async def search_finance(
            query: str,
            search_depth: Literal["basic", "advanced"] = "basic",
            time_range: Literal["day", "week", "month", "year"] = None,
            start_date: str = None,
            end_date: str = None,
            days: int = None,
            max_results: int = 5,
            include_domains: Sequence[str] = None,
            exclude_domains: Sequence[str] = None,
            include_answer: Union[bool, Literal["basic", "advanced"]] = None,
            include_raw_content: Union[bool, Literal["markdown", "text"]] = None,
            include_images: bool = None,
            timeout: int = 60,
            country: str = None,
        ):
            """
            Search Finance Information with Tavily API.

            Args:
                query : Search Query
                search_depth : Search Depth (basic, advanced)
                time_range : Search Time Range (day, week, month, year)
                start_date : Start Date (YYYY-MM-DD)
                end_date : End Date (YYYY-MM-DD)
                days : Search Days (1-30)
                max_results : Maximum Results (1-100)
                include_domains : Include Domains (List of Strings)
                exclude_domains : Exclude Domains (List of Strings)
                include_answer : Include Answer (True, False)
                include_raw_content : Include Raw Content (True, False)
                include_images : Include Images (True, False)
                timeout : Timeout (seconds)
                country : Country (ISO 3166-1 alpha-2)
            """
            try:
                self.logger.info(f"Calling 'search_finance' tool with query: '{query}'")
                result = await self.tavily_client.search(
                    query=query,
                    search_depth=search_depth,
                    topic='finance',
                    time_range=time_range,
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                    max_results=max_results,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content,
                    include_images=include_images,
                    timeout=timeout,
                    country=country,
                )
                self.logger.info(f"Search finance results: {len(result)}")
                return result
            except Exception as error:
                self.logger.error(f"Error in 'search_finance': {error}")
                return self.create_error_response(
                    error=error,
                    query=query,
                    func_name="search_finance"
                )

        @self.mcp.tool()
        async def search_news(
            query: str,
            search_depth: Literal["basic", "advanced"] = "basic",
            time_range: Literal["day", "week", "month", "year"] = None,
            start_date: str = None,
            end_date: str = None,
            days: int = None,
            max_results: int = 5,
            include_domains: Sequence[str] = None,
            exclude_domains: Sequence[str] = None,
            include_answer: Union[bool, Literal["basic", "advanced"]] = None,
            include_raw_content: Union[bool, Literal["markdown", "text"]] = None,
            include_images: bool = None,
            timeout: int = 60,
            country: str = None,
        ):
            """
            Search News with Tavily API.

            Args:
                query : Search Query
                search_depth : Search Depth (basic, advanced)
                time_range : Search Time Range (day, week, month, year)
                start_date : Start Date (YYYY-MM-DD)
                end_date : End Date (YYYY-MM-DD)
                days : Search Days (1-30)
                max_results : Maximum Results (1-100)
                include_domains : Include Domains (List of Strings)
                exclude_domains : Exclude Domains (List of Strings)
                include_answer : Include Answer (True, False)
                include_raw_content : Include Raw Content (True, False)
                include_images : Include Images (True, False)
                timeout : Timeout (seconds)
                country : Country (ISO 3166-1 alpha-2)
            """
            try:
                self.logger.info(f"Calling 'search_news' tool with query: '{query}'")
                result = await self.tavily_client.search(
                    query=query,
                    search_depth=search_depth,
                    topic='news',
                    time_range=time_range,
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                    max_results=max_results,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                    include_answer=include_answer,
                    include_raw_content=include_raw_content,
                    include_images=include_images,
                    timeout=timeout,
                    country=country,
                )
                self.logger.info(f"Search news results: {len(result)}")
                return result
            except Exception as error:
                self.logger.error(f"Error in 'search_news': {error}")
                return self.create_error_response(
                    error=error,
                    query=query,
                    func_name="search_news"
                )

def create_app() -> Any:
    server = TavilyMCPServer(
        server_name="tavily-search",
        server_instructions="Tavily Search Server is a MCP Server that provides search capabilities for web, news, and finance information.",
        server_version="0.1.0",
        transport="streamable_http",
        json_response=False,
    )

    return server.create_app()
    