"""
Base MCP Server Class.
"""

import time
import logging

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal

from abc import ABC, abstractmethod

from fastmcp.server.http import StarletteWithLifespan
from fastmcp.server.middleware import Middleware, MiddlewareContext

from starlette.requests import Request
from starlette.responses import JSONResponse

# ------------------------------------------------------------------------------------------------
# Standard Succuess/Error Response Models.
# ------------------------------------------------------------------------------------------------
class ResponseModel(BaseModel):
    """
    Standard Success response Model.

    Args:
        success: Boolean value of Success/Failure.
        data: Data contents for Request.
        query: Requested initial query.
    """

    model_config = ConfigDict(extra='allow')

    success = Field(..., description="Boolean value of Success/Failure.")
    data = Field(None, description="Data contents for Request.")
    query = Field(..., description="Requested initial query.")

class ErrorResponseModel(BaseModel):
    """
    Standard Error response model.

    Args:
        success: Boolean value of Success/Failure (always False).
        error: Error Message occured during requested process.
        query: Requested initial query.
        func_name: Function name that error occured.
    """
    
    model_config = ConfigDict(extra='allow')

    success = Field(False, description="Boolean value of Success/Failure (always False).")
    error = Field(..., description="Error Message occured during requested process.")
    query = Field(..., description="Requested initial query.")
    func_name = Field(None, description="Function name that error occured.")




# ------------------------------------------------------------------------------------------------
# Base MCP Server Class
# ------------------------------------------------------------------------------------------------
class BaseMCPServer(ABC):
    """
    Base MCP Server Class.

    Each MCP Server should implement based on this class.
    Implment common features of all mcp servers.
    """

    MCP_PATH = "/mcp"

    def __init__(
        self,
        server_name:str|None=None,
        server_instruction:str|None=None,
        transport:Literal["streamable-http", "stdio"]="streamable-http"
    ) -> None:
        
        from fastmcp import FastMCP

        # create FastMCP Instance
        self.mcp = FastMCP(
            name=server_name,
            instructions=server_instruction,
        )

        # Add Logger in fastmcp context
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - line %(lineno)s in %(filename)s : %(message)s'))
        self.logger.addHandler(stream_handler)
        self.mcp.logger = self.logger

        # set transport method
        self.transport = transport

        # Initialize MCP Tool clients
        self._initialize_clients()

        # Registry MCP Tools
        self._registry_tools()

        # Add Middlewares
        self.install_middlewares()
    

    # ------------------------------------------------------------------------------------------------
    # Settings for MCP Tools. Should implement specifics for specific MCP Server.
    # ------------------------------------------------------------------------------------------------
    @abstractmethod
    def _initialize_clients(self)->None:
        """
        Initialize MCP Tool clients.
        """
        raise NotImplementedError("Initialize Method for MCP Tools should be implemented.")
    
    @abstractmethod
    def _registry_tools(self)->None:
        """
        Define and Registry MCP Tools in Server.
        """
        raise NotImplementedError("MCP Tools should be defined and registred.")
    
    # ------------------------------------------------------------------------------------------------
    # Create Server's Success/Error Response with Standard Response Models.
    # ------------------------------------------------------------------------------------------------
    async def create_response(
        self,
        query:str,
        success:bool = True,
        data: str | Any | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Create Success Response with Standard Response Models.

        Args:
            success: Boolean value of Success/Failure.
            data: Data contents for Request.
            query: Requested initial query.
            **kwargs: extra fields.
        """
        _response = ResponseModel(
            success=success,
            query=query,
            data=data,
            **kwargs
        )

        return _response.model_dump(exclude_none=True)
    
    async def create_error_response(
        self,
        error: str,
        query: str,
        func_name:Any|None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Create Error Response with Standard Response Models.

        Args:
            success: Boolean value of Success/Failure (always False).
            error: Error Message occured during requested process.
            query: Requested initial query.
            func_name: Function name that error occured.
            **kwargs: extra fields.
        """
        _error_response = ErrorResponseModel(
            success=False,
            error=error,
            query=query,
            func_name=func_name,
            **kwargs
        )

        return _error_response.model_dump(exclude_none=True)
    
    # ------------------------------------------------------------------------------------------------
    # Create Starllete ASGI server app.
    # ------------------------------------------------------------------------------------------------
    async def create_app(self) -> StarletteWithLifespan:
        """
        Create Http app (Starlette ASGI Server app)
        """

        if not getattr(self, "_health_endpoint_added", None):
            self.mcp.custom_route("/health", methods=["GET"], include_in_schema=True)
            async def health_check(request:Request)->JSONResponse:
                _response = ResponseModel(
                    success=True,
                    data="ok",
                    query="MCP Server Health Check."
                )

                return JSONResponse(_response)
            
            setattr(self, "_health_endpoint_added", True)
        
        return self.mcp.http_app(
            path=self.MCP_PATH,
            transport=self.transport
        )
    
    # ------------------------------------------------------------------------------------------------
    # Add Middleware in MCP Server.
    # ------------------------------------------------------------------------------------------------
    def install_middlewares(self)->None:
        """
        Add MCP Server Middelwares in server.
        
        middleware list:
            ErrorHandlerMiddleware
            LoggingMiddleware
            TimingMiddelware
        """
        
        self.mcp.add_middleware(self.ErrorHandlingMiddleware)
        self.mcp.add_middleware(self.TimingMiddelware)
        self.mcp.add_middleware(self.LoggingMiddleware)
    
    # ------------------------------------------------------------------------------------------------
    # Core Middleware Classes.
    # ------------------------------------------------------------------------------------------------
    class ErrorHandlingMiddleware(Middleware):
        """
        Error Event Handling Middleware.
        """

        async def on_call_tool(self, context:MiddlewareContext, call_next):
            
            try:
                return await call_next(context=context)
            except Exception as error:
                try:
                    server = context.fastmcp_context.fastmcp
                    logger = getattr(server, "logger", None)

                    if logger:
                        logger.error(f"Tool Error : {error}", exc_info=True)
                    else:
                        raise UserWarning('Logger is not Setted in this MCP Server.')
                except Exception as error:
                    raise error
    
    class LoggingMiddleware(Middleware):
        """
        Middleware for Log Process in MCP Server.
        """

        async def on_call_tool(self, context:MiddlewareContext, call_next):
            try:
                server = context.fastmcp_context.fastmcp
                logger = getattr(server, "logger", None)

                if logger:
                    meta = {
                        'request_id' : getattr(context.fastmcp_context, "request_id", None),
                        'client_id' : getattr(context.fastmcp_context, 'client_id', None),
                        'session_id' : getattr(context.fastmcp_context, 'session_id', None)
                    }
                    logger.info(f"Start Process for Request : {meta}")
                else:
                    UserWarning("Logger is not Setted in this MCP Server.")
                
                response = await call_next(context=context)

                if logger:
                    duration_ms = context.fastmcp_context.get_state('duration_ms')
                    logger.info(f"Requst Succeed for duration time (ms) : {duration_ms}")
                else:
                    UserWarning("Logger is not Setted in this MCP Server.")
                
                return response
            except Exception as error:
                raise error
    
    class TimingMiddelware(Middleware):
        """
        Middleware for Calculation Processing time
        """

        async def on_call_tool(self, context:MiddlewareContext, call_next):

            start_time = time.perf_counter()

            try : 
                return await call_next(context=context)
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                try:
                    context.fastmcp_context.set_state('duration_ms', duration_ms)
                except Exception as error:
                    raise error