FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

RUN pip install fastmcp>=2.11.0
RUN pip install langchain>=0.3.27
RUN pip install langchain-mcp-adapters>=0.1.9
RUN pip install langchain-openai>=0.3.28
RUN pip install langgraph>=0.6.2
RUN pip install python-dotenv>=1.1.1
RUN pip install tavily-python>=0.3.8
RUN pip install uvicorn[standard]>=0.32.0

COPY ./src/ ./src/

ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV LOG_LEVEL=info

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE 3000

ENTRYPOINT ["uvicorn"]
CMD ["mcp_servers.tavily_search.server:create_app", "--host", "0.0.0.0", "--port", "3000", "--factory"]