from argparse import OPTIONAL
from dataclasses import dataclass
import os
from enum import Enum
from typing import Optional, Dict, List, Any

# class EnvVarType(Enum):
#     """
#     Type of environment variable
#     """
#     REQUIRED = "required"
#     OPTIONAL = "optional"
#     CONDITIONAL = "conditional"

# @dataclass
# class EnvVarSpec:
#     """
#     Environment Variable Specification
#     """

#     name: str
#     var_type: EnvVarType
#     desciption: str
#     default: Optional[str] = None
#     validator: Optional[callable] = None
#     sensitive: bool = False
#     depends_on: Optional[List[str]] = None
    

def get_env_variable(key: str, default: str | None = None) -> str:
    return os.getenv(key, default)