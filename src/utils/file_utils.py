"""
File utility functions.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

from .logger import get_logger

logger = get_logger(__name__)


def ensure_directory(directory: Union[Path, str]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory) if isinstance(directory, str) else directory
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Dict[str, Any], filepath: Union[Path, str], indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Path to the JSON file
        indent: JSON indentation level
    """
    path = Path(filepath)
    ensure_directory(path.parent)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    logger.debug(f"Saved JSON to {path}")


def load_json(filepath: Union[Path, str]) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data
    """
    path = Path(filepath)
    
    if not path.exists():
        logger.error(f"JSON file not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.debug(f"Loaded JSON from {path}")
    return data
