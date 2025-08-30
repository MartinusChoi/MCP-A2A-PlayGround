"""
Base MCP Server Class.
"""

import time
from abc import ABC, abstractmethod
import logging
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.http import StarletteWithLifespan
from starlette.requests import Request
from starlette.responses import JSONResponse

# -----------------------------------------------------------
# Standard Response Model
# -----------------------------------------------------------
class StandardResponse(BaseModel):
    """
    Standard MCP Server Response Model.
    """

    model_config = ConfigDict(extra='allow')

    success: bool = Field(..., description="Boolean Value of Success or Failure")
    query: str = Field(..., description="User's Initial Query")
    data: Any | None = Field(None, description="Response Data (Success)")
    error: str | None = Field(None, description="Error Message (Failure)")

class StandardErrorResponse(BaseModel):
    """
    Standard MCP Server Error Response Model.
    """

    model_config = ConfigDict(extra='allow')

    success: bool = Field(False, description="Boolean Value of Success or Failure (Always False)")
    query: str = Field(..., description="User's Initial Query")
    error: str = Field(..., description="Error Message")
    func_name: str | None = Field(None, description="Function Name that Caused Error")

# -----------------------------------------------------------
# Base MCP Server Class
# -----------------------------------------------------------
class BaseMCPServer(ABC):
    """Base MCP Server Class"""

    MCP_PATH = '/mcp/'

    def __init__(
        self,
        server_name: str | None = None,
        server_instructions: str | None = None,
        server_version: str | None = None,
        transport: Literal['streamable_http', 'stdio'] = 'streamable_http',
        json_response: bool = False,
        enable_swagger: bool = False,
    ):
        """
        Initialize MCP Server.

        Args:
            server_name: Name of MCP Server
            server_instructions: Instructions of MCP Server
        """

        from fastmcp import FastMCP

        self.server_name = server_name
        self.server_instructions = server_instructions
        self.server_version = server_version
        self.transport = transport
        self.json_response = json_response
        self.enable_swagger = enable_swagger

        # Create FastMCP Instance
        self.mcp = FastMCP(
            name = self.server_name or self.__class__.__name__,
            instructions = self.server_instructions,
        )

        # Create Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s > %(message)s'))
        self.logger.addHandler(stream_handler)
        self.mcp.logger = self.logger

        # Initialize Clients
        self._initialize_clients()

        # Register Tools
        self._register_tools()

        # Install Core Middlewares
        self._install_core_middlewares()
    
    # -----------------------------------------------------------
    # Should Implement in each MCP Server
    # -----------------------------------------------------------
    @abstractmethod
    def _initialize_clients(self) -> None:
        """Initialize Client Instaces."""
        pass

    @abstractmethod
    def _register_tools(self) -> None:
        """Register MCP Tools."""
        pass

    # -----------------------------------------------------------
    # Create Standard / Error Response
    # -----------------------------------------------------------
    def create_standard_response(
        self,
        success: bool,
        query: str,
        data: Any | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """
        Create Response based on Standard Response Model.
        
        Args:
            success: Boolean Value of Success or Failure
            query: User's Initial Query
            data: Response Data (Success)
            error: Error Message (Failure)
        """

        # create response model instance
        _response = StandardResponse(
            success = success,
            query = query,
            data = data,
            error = error,
        )
        # serialize response model instance
        response = _response.model_dump(exclude_none=True)

        return response
    
    def create_error_response(
        self,
        error: Exception,
        query: str,
        func_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create Error Response based on Standard Error Response Model.
        
        Args:
            error: Error Message
            query: User's Initial Query
            func_name: Function Name that Caused Error
        """

        # create error response model instance
        _error_response = StandardErrorResponse(
            error = str(error),
            query = query,
            func_name = func_name,
            success = False,
        )
        # serialize error response model instance
        error_response = _error_response.model_dump(exclude_none=True)

        return error_response

    # -----------------------------------------------------------
    # Create Server Instance
    # -----------------------------------------------------------
    def create_app(self) -> StarletteWithLifespan:
        """
        Create ASGI(Starlette) Application with Lifespan.

        - register /health route only once.
        - return http_app of FastMCP
        """

        if not getattr(self, "_health_route_registered", False):
            @self.mcp.custom_route(path='/health', methods=['GET'], include_in_schema=True)
            async def health_check(request: Request) -> JSONResponse:
                _response = self.create_standard_response(
                    success=True,
                    query="MCP Server Health Check",
                    data="OK",
                )
                return JSONResponse(content=_response)
            setattr(self, "_health_route_registered", True)
        
        return self.mcp.http_app(
            path=self.MCP_PATH,
            json_response=self.json_response
        )
    
    # -----------------------------------------------------------
    # Install Core Middlewares
    # -----------------------------------------------------------
    def _install_core_middlewares(self) -> None:
        """
        Install Core Middleware Classes in Server.
        """
        # Install error handling middleware with server reference
        self.mcp.add_middleware(self.ErrorHandlingMiddleware())
        self.mcp.add_middleware(self.TimingMiddleware())
        self.mcp.add_middleware(self.LoggingMiddleware())
    
    # -----------------------------------------------------------
    # Core Middleware Classes
    # -----------------------------------------------------------
    class ErrorHandlingMiddleware(Middleware):
        """
        Error Handling Middleware Class.
        """

        async def on_call_tool(
            self,
            context: MiddlewareContext,
            call_next
        ) -> dict[str, Any]:
            """
            Handle Error in Tool Call.

            Args:
                context: Middleware Context
                call_next (Callable): Next Middleware or Tool Call
            """

            try:
                return await call_next(context=context)

            except Exception as error:
                # Try convert Exception into standard error response model
                try:
                    # Logging Error Message
                    server = context.fastmcp_context.fastmcp
                    logger = getattr(server, "logger", None)
                    if logger:
                        logger.error(f"ToolError : {error}", exec_info=True)
                    else:
                        logger.warning("Logger Not Found in Server")
                except Exception:
                    pass

                raise # FastMCP will handle the error and return the error response

    class LoggingMiddleware(Middleware):
        """
        Logging Middleware Class.
        """

        async def on_call_tool(
            self,
            context: MiddlewareContext,
            call_next
        ) -> dict[str, Any]:
            try:
                # Get logger
                server = context.fastmcp_context.fastmcp
                logger = getattr(server, "logger", None)

                # Logging Start Processing Tool Request
                if logger:
                    meta = {
                        "request_id" : getattr(context.fastmcp_context, "request_id", None),
                        "client_id" : getattr(context.fastmcp_context, "client_id", None),
                        "session_id" : getattr(context.fastmcp_context, "session_id", None),
                    }
                    logger.info(f"Start Processing Tool Request : {meta}")
                else:
                    logger.warning("Logger Not Found in Server")

                response = await call_next(context=context)

                # Logging Success Response
                if logger:
                    try:
                        duration_ms = context.fastmcp_context.get_state("duration_ms")
                        logger.info(f"Successfully Processed Tool Request : duration_ms={duration_ms}")
                    except Exception:
                        pass
                
                return response
            except Exception:
                raise
        
    class TimingMiddleware(Middleware):
        """
        Calculate Processing Time of Tool Call.
        """

        async def on_call_tool(
            self,
            context: MiddlewareContext,
            call_next
        ):
            start = time.perf_counter()

            try:
                return await call_next(context=context)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000.0
                try:
                    context.fastmcp_context.set_state("duration_ms", duration_ms)
                except Exception:
                    pass