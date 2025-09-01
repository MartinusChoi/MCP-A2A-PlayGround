"""
Base MCP Server Class

Each MCP Server Should Implement Based on this Base Server Class
"""

from abc import ABC, abstractmethod
import logging

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Any
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastmcp.server.http import StarletteWithLifespan
from fastmcp.server.middleware import Middleware, MiddlewareContext

# -----------------------------------------------------------------------
# Standard MCP Server Response Model
# -----------------------------------------------------------------------
class ResponseModel(BaseModel):
    """
    Standard MCP Server Response Model.
    """

    model_config = ConfigDict(extra='allow')

    success = Field(..., description="Boolean Value of Success of Failure")
    query = Field(..., description="Requested Query from Client")
    data = Field(None, descripttion="Response Data of Client Request")

class ErrorResponseModel(BaseModel):
    """
    Standard MCP Server Error Respnose Model
    """

    model_config = ConfigDict(extra='allow')

    success = Field(False, description="Boolean value of Success or Failure (Always False)")
    error = Field(..., description="Error Message")
    func_name = Field(None, description="Function name that error occured")
    

# -----------------------------------------------------------------------
# Base MCP Server Class
# -----------------------------------------------------------------------
class BaseMCPServer(ABC):
    MCP_PATH = '/mcp/'

    def __init__(
        self,
        server_name: str | None = None,
        server_instruction: str | None = None,
        server_version: str | None = None,
        transport: Literal['streamable-http', 'stdio'] = 'streamable-http'
    )->None:
        """
        Initialize Server Instance

        Args:
            server_name: str | None = None : MCP Server Name
            server_instruction: str | None = None : MCP Server instruction
            server_version: str | None = None : MCP Server version
        """

        from fastmcp import FastMCP

        # create fastmcap instance
        self.mcp = FastMCP(
            nams=server_name,
            instructions=server_instruction,
            version=server_version,
        )

        self.transport = transport

        # set logger in mcp context
        logger = logging.getLogger(server_name or self.__class__.__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())
        self.mcp.logger = logger

        # initialize client
        self._initialize_clients()

        # register mcp tools
        self._register_tools()
    

    # -----------------------------------------------------------------------
    # Should Implement before Using
    # -----------------------------------------------------------------------
    def _initialize_clients(self)->None:
        """
        Initialize Client
        """
        pass

    def _register_tools(self)->None:
        """
        Register MCP Tools
        """
        pass

    # -----------------------------------------------------------------------
    # create response
    # -----------------------------------------------------------------------
    def create_response(
        self,
        success:bool,
        query:str,
        data:str|None=None
    )->dict[str, Any]:
        """
        Create Response.

        Args:
            success = Boolean Value of Success of Failure
            query = Requested Query from Client
            data = Response Data of Client Request
        """

        _response = ResponseModel(
            success=success,
            query=query,
            data=data
        )

        return _response.model_dump(exclude_none=True)
    
    def create_error_response(
            self,
            error:str,
            func_name:str|None=None,
    )-> dict[str, Any]:
        """
        Create Error Response

        Args:
            error = Error Message
            func_name = Function name that error occured
        """
        _error_response = ErrorResponseModel(
            successs=False,
            error=error,
            func_name=func_name
        )

        return _error_response.model_dump(exclude_none=True)


    # -----------------------------------------------------------------------
    # create server instance
    # -----------------------------------------------------------------------
    def create_app(self)->StarletteWithLifespan:
        if getattr(self, "_health_endpoint_registered", None):
            @self.mcp.custom_route("/health", methods=["GET"], include_in_schema=True)
            async def is_healthy(request:Request)->JSONResponse:
                _response = ResponseModel(
                    success=True,
                    query="MCP Server Health Check",
                    data="OK"
                )

                return JSONResponse(_response)
            setattr(self, "_health_endpoint_registered", True)
        
        return self.mcp.http_app(
            path=self.MCP_PATH,
            transport=self.transport,
        )
    
    # -----------------------------------------------------------------------
    # add middleware in mcp server
    # -----------------------------------------------------------------------
    def add_middleware(self)->None:
        """
        Add Middlewares in MCP Server
        """

        self.mcp.add_middleware()
        self.mcp.add_middleware()
        self.mcp.add_middleware()
    
    # -----------------------------------------------------------------------
    # Core Middle Ware Class
    # -----------------------------------------------------------------------
    class ErrorHandlingMiddleware(MiddlewareContext):
        async def on_call_tool(self, context:MiddlewareContext, call_next):
            try:
                return await call_next(context=context)
            except Exception as error:
                # Try Convert Error message into standrade error response model
                try:
                    server = context.fastmcp_context.fastmcp
                    logger = getattr(server, "logger", None)

                    if logger:
                        logger.error(f"Tool Error Occured : {error}")
                except:
                    pass