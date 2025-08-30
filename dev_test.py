import asyncio
import os
from dotenv import load_dotenv
from src.mcp_servers.tavily_search.client import TavilySearchClient

load_dotenv()

tavily_client = TavilySearchClient()

result = asyncio.run(tavily_client.search(query="OpenAI 2025 August latest open source model"))