"""
Tavily Search Client.
"""

from src.utils.env_validator import get_env_variable

import logging
from typing import Any, Literal, Sequence, Union, cast

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s > %(message)s'))
logger.addHandler(stream_handler)

class TavilySearchClient:
    """
    Tavliy Web Search Client.
    """

    def __init__(
        self,
    ):
        """
        Initialize Tavily Search Client.

        Args:
            api_key : Tavily API Key (Get from env if not provided)
        """

        self.api_key = get_env_variable("TAVILY_API_KEY", "INPUT_YOUR_API_KEY")

        if self.api_key == "INPUT_YOUR_API_KEY":
            logger.warning("Tavily API Key is not set. Please set TAVILY_API_KEY in env.")
    
    async def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = None,
        topic: Literal["general", "news", "finance" ] = None,
        time_range: Literal["day", "week", "month", "year"] = None,
        start_date: str = None,
        end_date: str = None,
        days: int = None,
        max_results: int = None,
        include_domains: Sequence[str] = None,
        exclude_domains: Sequence[str] = None,
        include_answer: Union[bool, Literal["basic", "advanced"]] = None,
        include_raw_content: Union[bool, Literal["markdown", "text"]] = None,
        include_images: bool = None,
        timeout: int = 60,
        country: str = None,
    ) -> dict[str, Any]:
        """
        Search Web with Tavily API.

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
            **kwargs : Additional Arguments (Accept custom arguments)

        Returns:
            dictionary of Search Results
        """
        from tavily import TavilyClient

        # initialize tavily client
        client = TavilyClient(api_key=self.api_key)

        # set search parameters
        search_params = {
            'query' : query,
            'max_results' : max_results,
            'search_depth' : search_depth,
            'topic' : topic or "general",
            'time_range' : time_range,
            'start_date' : start_date,
            'end_date' : end_date,
            'days' : days,
            'include_domains' : include_domains,
            'exclude_domains' : exclude_domains,
            'include_answer' : include_answer,
            'include_raw_content' : include_raw_content,
            'include_images' : include_images,
            'timeout' : timeout,
            'country' : country,
        }
        
        # Execute Search
        results = client.search(**search_params)

        logger.info(f"Search Results: {len(results)}")

        return cast(dict[str, Any], results)
