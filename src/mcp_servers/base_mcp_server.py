"""
Base MCP Server Class

모든 MCP Server가 상속받아 사용할 수 있는 Base MCP Server Class를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Literal, Any
import logging
from pydantic import BaseModel, Field, ConfigDict
import time
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.http import StarletteWithLifespan
from starlette.requests import Request
from starlette.responses import JSONResponse

# -----------------------------------------------------------
# Standard Response / Error Model
# -----------------------------------------------------------
class StandardResponse(BaseModel):
    """Standard MCP Server Response Model"""

    # Allow add new field for Response Model
    model_config = ConfigDict(extra="allow")

    success: bool = Field(..., description='성공 여부') # essential field
    query: str = Field(..., description='원본 쿼리') # essential field
    data: Any | None = Field(None, description='응답 데이터 (성공 시)')
    error: str | None = Field(None, description='에러 메시지 (실패 시)')

class ErrorResponse(BaseModel):
    """Standard MCP Server Error Response Model"""

    # Allow add new field for error response model
    model_config = ConfigDict(extra='allow')

    query: str = Field(..., description='원본 쿼리')
    error: str = Field(..., description='에러 메시지')
    func_name: str | None = Field(None, description='에러가 발생한 함수 이름')

# -----------------------------------------------------------
# Base MCP Server Class
# -----------------------------------------------------------
class BaseMCPServer(ABC):
    """
    Base Class for all MCP Server.

    Every MCP Server Shold Define Server class with this Base Server Class.
    """

    MCP_PATH = '/mcp/'

    def __init__(
        self,
        server_name: str = None,
        server_instructions: str | None = None,
        server_version: str = None,
        transport: Literal['streamable-http', 'stdio'] = 'streamable-http',
        json_response: bool = False,
    ):
        """
        Initialize MCP Server.

        Args:
            server_name: Name of Server (Essential)
            server_instruction: Decription of Server (Essential) 
            server_version: Version Information of MCP Server
            transport: MCP Transmision Method (default: "streamable-http")
        """

        from fastmcp import FastMCP

        self.server_name = server_name
        self.server_instructions = server_instructions
        self.server_version = server_version
        self.transport = transport
        self.json_response = json_response

        # Create FastMCP Instance
        self.mcp = FastMCP(
            name = self.server_name,
            instructions = self.server_instructions
        )

        # Set Logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize client
        self._initialize_clients()

        # Regist Tools
        self._register_tools()

        # install Essential Middleware
        self._install_core_middlewares()
    
    # -----------------------------------------------------------
    # Should Implement in each MCP Server
    # -----------------------------------------------------------
    
    @abstractmethod
    def _initialize_clients(self) -> None:
        """Initialize Client Instance."""
        pass

    @abstractmethod
    def _register_tools(self) -> None:
        """Register MCP Tools."""
        pass

    # -----------------------------------------------------------
    # Create Response / Error
    # -----------------------------------------------------------

    def create_standard_response(
        self,
        success: bool,
        query: str,
        data: Any = None,
        error: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Create Response Format according to 'StandardResponse' Class

        Args:
            success: Succes for Failure (Boolean)
            query : Original query of User
            data : Response data
            error : Error message
            **kwargs : Any additional response fields
        
        Returns:
            dict instance with standard structure (can be serialized to JSON)
        """

        response_model = StandardResponse(
            success=success,
            query=query,
            daat=data,
            error=error,
            **kwargs
        )
        # convert BaseModel Instance into Dictionary
        response_dict = response_model.model_dump(exclude_none=True)

        return response_dict
    
    async def handle_error(
        self,
        func_name: str,
        error: Exception,
        **context
    ) -> dict[str, Any]:
        """
        Standard Error Handle Function.

        Args:
            func_name: Function Name that Error has occured
            error: Error message
            **context: Context information of Error
        
        Returns:
            dictionary of Error Response
        """

        self.logger.error(
            f"Error Occured Poine > {func_name} | Error Message : {error}", 
            exc_info=True # Add TraceBack Message in Logging Message
        )

        error_model = ErrorResponse(
            query=context.get("query", ""),
            error=str(error),
            func_name=func_name,
            **{key:value for key, value in context.items() if key != 'query'}
        )
        error_dict = error_model.model_dump(exclude_none=True)

        return error_dict
    
    # -----------------------------------------------------------
    # Create Server Instance
    # -----------------------------------------------------------
    def create_app(self) -> StarletteWithLifespan:
        """
        Create ASGI app
        - register /health route only once.
        - return http_app of FastMCP
        """
        if not getattr(self, "_health_route_registered", False):
            @self.mcp.custom_route(path='/health', methods=["GET"], include_in_schema=True)
            async def health_check(request: Request) -> JSONResponse:
                response_data = self.create_standard_response(
                    success=True,
                    query="MCP Server Health check",
                    data="OK"
                )
                return JSONResponse(content=response_data)
            setattr(self, "_health_route_registered", True)
        
        return self.mcp.http_app(
            path=self.MCP_PATH,
            json_response=self.json_response
        )


    # -----------------------------------------------------------
    # Core MiddleWare
    # -----------------------------------------------------------
    @abstractmethod
    def _install_core_middlewares(self) -> None:
        """Install Core Middleware Classes in Server"""
        self.mcp.add_middleware(self.ErrorHandlingMiddleware())
        self.mcp.add_middleware(self.TimingMiddleware())
        self.mcp.add_middleware(self.LoggingMiddleware())

    class ErrorHandlingMiddleware(Middleware):
        async def on_call_tool(
            self,
            context: MiddlewareContext,
            call_next
        ):
            try:
                return await call_next()
            except Exception as error:
                # Conver into Standard Error Response
                try:
                    server = context.fastmcp_context.fastmcp # get mcp server instance
                    logger = getattr(server, "logger", None)
                    if logger:
                        logger.error(f"Tool Error : {error}", exc_info=True)
                except Exception:
                    pass

                raise
    
    class TimingMiddleware(Middleware):
        async def on_call_tool(self, context: MiddlewareContext, call_next):
            start = time.perf_counter()
            try:
                return await call_next()
            finally:
                duration_ms = (time.perf_counter() - start) * 1000.0
                try:
                    context.fastmcp_context.set_state("duration_ms", duration_ms)
                except Exception:
                    pass

    class LoggingMiddleware(Middleware):
        async def on_call_tool(self, context: MiddlewareContext, call_next):
            try:
                server = context.fastmcp_context.fastmcp
                logger = getattr(server, "logger", None)
                if logger:
                    meta = {
                        "request_id": getattr(context.fastmcp_context, "request_id", None),
                        "client_id": getattr(context.fastmcp_context, "client_id", None),
                        "session_id": getattr(context.fastmcp_context, "session_id", None),
                    }
                    logger.info(f"Tool call start: {meta}")
                result = await call_next()
                if logger:
                    duration_ms = context.fastmcp_context.get_state("duration_ms")
                    logger.info(f"Tool call end: duration_ms={duration_ms}")
                return result
            except Exception:
                raise