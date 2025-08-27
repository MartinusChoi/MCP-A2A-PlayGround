"""Tavily Search API Simulation And Tools"""

import os
import logging
from typing import List, Any, Literal, cast

from src.utils.env_validator import get_optional_env

logger = logging.getLogger(__name__)

class TavilySearchAPI:
    """
    Tavliy Search API Client

    Client that search recent information with Tavily AI's real-time web search API.
    it provide various topics for search such as 'news', 'general', 'finance'... etc.
    And it also provide advanced searching options like time range, domain filtering...
    """

    def __init__(
            self,
            api_key:str | None = None
    ):
        """
        Initialize Taily AI Client

        Args:
            api_key : Tavily AI API key (Read in Environment Value if api_key is 'None')
        """
        self.api_key = api_key or get_optional_env("TAVILY_API_KEY", "INPUT_YOUR_API_KEY")

        # validation api key
        if self.api_key == "INPUT_YOUR_API_KEY":
            logger.warning(
                "Tavily API key not set. Please set TAVILY_API_KEY environment variable."
            )
    
    async def search(
            self,
            query: str,
            search_depth: Literal["basic", "advanced"] = "basic",
            max_results: int = 5,
            topic: Literal["general", "news", "finance"] | None = None,
            time_range: Literal["day", "week", "month", "year"] | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
            days: int | None = None,
            include_domains: List[str] | None = None,
            exclude_domains: List[str] | None = None,
    ) -> dict[str, Any]:
        """
        Tavily Search API: Real-Time Web Search
        
        Performs real-time web searches to retrieve the latest information.
        Provides accurate and relevant results using various filtering options.
        
        Args:
	        query: Search keyword or question.
	        search_depth: Search depth.
	            basic: Quick search with basic results.
	            advanced: In-depth search with more data and analysis.
	        max_results: Maximum number of results to return (range: 1–100).
	        topic: Filter by search topic.
	            general: General web search.
	            news: News and current affairs.
	            finance: Financial and economic information.
	        time_range: Time range for search.
	            day: Past 1 day.
	            week: Past week.
	            month: Past month.
	            year: Past year.
	        start_date: Search start date (YYYY-MM-DD format).
	        end_date: Search end date (YYYY-MM-DD format).
	        days: Return results from the last N days (integer).
	        include_domains: List of domains to include.
	            Example: ["wikipedia.org", "github.com"]
	        exclude_domains: List of domains to exclude.
	            Example: ["ads.com", "spam.com"]

        Returns:
            List[Dictstr, Any]: List of search results.Each result includes:
	            title: Page title
	            url: Page URL
	            content: Summary of page content
	            score: Relevance score
	            published_date: Published date (if available)
        
        Raises:
            Exception: On API call failure or network error
        """
        from tavily import TavilyClient

        client = TavilyClient(api_key=self.api_key)

        search_param = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        search_param["topic"] = topic or "general"
        search_param["time_range"] = time_range or None
        search_param["start_date"] = start_date or None
        search_param["end_date"] = end_date or None
        search_param["days"] = days or None
        search_param["include_domains"] = include_domains or None
        search_param["exclude_domains"] = exclude_domains or None

        search_result = client.search(**search_param)

        return cast(dict[str, Any], search_result)