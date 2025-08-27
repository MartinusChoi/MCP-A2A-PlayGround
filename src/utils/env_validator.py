import os

def get_optional_env(key:str, default:str|None=None) -> str | None:
    return os.getenv(key, default)