"""Utility Functions for ALO System"""
import os
import json
import hashlib
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

def hash_string(text: str) -> str:
    """Generate MD5 hash of string"""
    return hashlib.md5(text.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely load JSON, return default on failure"""
    try:
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = text.strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return default

def count_tokens(text: str) -> int:
    """Rough token count (1 token ≈ 4 chars)"""
    return len(text) // 4
