import asyncio
import sys
import os
from uuid import uuid4
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.env_validator import get_env_variable
from src.agents.tavily.tavily_search_agent import TavilySearchAgent
from langchain_core.messages import (
    HumanMessage,
    AIMessage
)
from langchain_openai import ChatOpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


async def main():
    print("Starting Tavily Search Agent Experiment...")

    try:
        print("Creating Tavily Search Agent...")
        agent = await TavilySearchAgent.create(
            model=ChatOpenAI(model="gpt-4o", temperature=0),
            agent_name="TavilySearchAgent"
        )
        print("Agent created successfully!")
    except Exception as e:
        print(f"Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return

    query_list = [
        "OpenAI의 2025년 8월 기준 가장 최근에 공개된 오픈소스 모델에 대해 자세히 정리해주세요.",
        # "2025년 8월 기준 최신 AI 트렌드에 대해 조사하여 정리해주세요.",
        # "2025년 8월 29일 기준 최신 뉴스에 대해 조사하여 정리해주세요."
    ]

    for idx, query in enumerate(query_list):
        print("\n", "="*50)
        print(f"Processing query {idx+1} > {query}")
        print("\n", "="*50)

        try:
            agent_config = RunnableConfig(
                configurable={
                    "thread_id" : str(uuid4())
                }
            )

            async for chunk in agent.graph.astream({"messages": [HumanMessage(content=query)]}, config=agent_config):
                if isinstance(chunk, dict):
                    for node_state in chunk.values():
                        messages = node_state.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, HumanMessage):
                                print(f"Human: {msg.content}")
                            if isinstance(msg, AIMessage):
                                # 도구 호출 정보 출력
                                if msg.tool_calls:
                                    print("\n[도구 사용]")
                                    for tool_call in msg.tool_calls:
                                        print(
                                            f"  - {tool_call['name']}: {tool_call['args']}"
                                        )
                                    print()

                                if msg.content:
                                    print(msg.content)
        
        except Exception as e:
            print(f"Error processing query {idx+1}: {e}")
            import traceback
            traceback.print_exc()
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutdown Program by User")
    except Exception as error:
        print("Error occurred:", error)