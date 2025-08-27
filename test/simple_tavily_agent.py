import asyncio
import sys
import os
from uuid import uuid4
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from src.agents.tavily_search_agent.search_react_agent import SimpleTavilyMCPAgent, InputSchema, StateSchema, OutputState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(stream_handler)


async def main():
    logger.info("Creating Agent with Tavily MCP Client...")
    agent = await SimpleTavilyMCPAgent.create(
        model=ChatOpenAI(model="gpt-4o", temperature=0),
        state_schema=StateSchema,
        input_state=InputSchema,
        output_state=OutputState,
        checkpointer=MemorySaver(),
        max_retry_attempts=2,
        agent_name="simple_tavily_agent",
    )

    test_query = [
        "OpenAI의 2025년 8월 기준 가장 최근 오픈소스 공개 모델에 대해 조사하고 상세히 설명해줘."
    ]

    for idx, query in enumerate(test_query):
        pass