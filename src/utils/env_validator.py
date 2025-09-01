from argparse import OPTIONAL
from dataclasses import dataclass
import os
from enum import Enum
from typing import Optional, Dict, List, Any
    

def get_env_variable(key: str, default: str | None = None) -> str:
    return os.getenv(key, default)