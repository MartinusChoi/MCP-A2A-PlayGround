"""
Base MCP Server Class.
"""

import logging

from pydantic import BaseModel, ConfigDict, Field
from typing import Any

from abc import ABC, abstractmethod


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

    def __init__(
        self,
        server_name,
        server_instruction,
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

        # Initialize MCP Tool clients
        self._initialize_clients()

        # Registry MCP Tools
        self._registry_tools()

        # Add Middlewares
    

    # ------------------------------------------------------------------------------------------------
    # Settings for MCP Tools. Should implement specifics for specific MCP Server.
    # ------------------------------------------------------------------------------------------------
    def _initialize_clients(self)->None:
        """
        Initialize MCP Tool clients.
        """
        raise NotImplementedError("Initialize Method for MCP Tools should be implemented.")

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
    ) -> dict[str, Any]:
        _response = ResponseModel(
            success=success,
            query=query,
            data=data
        )

        return _response.model_dump(exclude_none=True)
    
    async def create_error_response(
        self,
        error: str,
        query: str,
        func_name:Any|None = None
    ) -> dict[str, Any]:
        _error_response = ErrorResponseModel(
            success=False,
            error=error,
            query=query,
            func_name=func_name
        )

        return _error_response.model_dump(exclude_none=True)
    
    
        