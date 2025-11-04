"""
Path constants and utilities for data file management.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional


# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
APPLICATIONS_DIR = DATA_DIR / "applications"
DEBUG_DIR = DATA_DIR / "debug"
LOGS_DIR = DATA_DIR / "logs"

# Screenshot subdirectories
PRE_SUBMIT_DIR = SCREENSHOTS_DIR / "pre_submit"
POST_SUBMIT_DIR = SCREENSHOTS_DIR / "post_submit"

# Debug subdirectories
FORM_HTML_DIR = DEBUG_DIR / "form_html"
FORM_SCREENSHOTS_DIR = DEBUG_DIR / "form_screenshots"


def ensure_data_directories():
    """Ensure all data directories exist."""
    directories = [
        DATA_DIR,
        SCREENSHOTS_DIR,
        PRE_SUBMIT_DIR,
        POST_SUBMIT_DIR,
        APPLICATIONS_DIR,
        DEBUG_DIR,
        FORM_HTML_DIR,
        FORM_SCREENSHOTS_DIR,
        LOGS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_timestamped_filename(prefix: str, extension: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate a timestamped filename.
    
    Args:
        prefix: Filename prefix (e.g., 'pre_submit', 'filled_application')
        extension: File extension without dot (e.g., 'png', 'json')
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Filename string like 'pre_submit_20251103_105621.png'
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp_str}.{extension}"


def get_pre_submit_screenshot_path(timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for pre-submit screenshot.
    
    Args:
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the screenshot
    """
    ensure_data_directories()
    filename = get_timestamped_filename("pre_submit", "png", timestamp)
    return PRE_SUBMIT_DIR / filename


def get_post_submit_screenshot_path(timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for post-submit screenshot.
    
    Args:
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the screenshot
    """
    ensure_data_directories()
    filename = get_timestamped_filename("post_submit", "png", timestamp)
    return POST_SUBMIT_DIR / filename


def get_application_data_path(timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for application JSON data, organized by date.
    
    Args:
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the application JSON file
    """
    ensure_data_directories()
    
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create date-based subdirectory (YYYY-MM-DD)
    date_folder = timestamp.strftime("%Y-%m-%d")
    app_dir = APPLICATIONS_DIR / date_folder
    app_dir.mkdir(parents=True, exist_ok=True)
    
    filename = get_timestamped_filename("filled_application", "json", timestamp)
    return app_dir / filename


def get_form_html_debug_path(timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for form HTML debug file.
    
    Args:
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the HTML file
    """
    ensure_data_directories()
    filename = get_timestamped_filename("form_html_debug", "html", timestamp)
    return FORM_HTML_DIR / filename


def get_form_debug_screenshot_path(timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for form debug screenshot.
    
    Args:
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the screenshot
    """
    ensure_data_directories()
    filename = get_timestamped_filename("form_debug", "png", timestamp)
    return FORM_SCREENSHOTS_DIR / filename


def get_log_file_path(log_type: str = "app", timestamp: Optional[datetime] = None) -> Path:
    """
    Get path for log file, organized by date.
    
    Args:
        log_type: Type of log ('app', 'error', 'debug')
        timestamp: Optional timestamp, defaults to now
        
    Returns:
        Path object for the log file
    """
    ensure_data_directories()
    
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create date-based subdirectory (YYYY-MM-DD)
    date_folder = timestamp.strftime("%Y-%m-%d")
    log_dir = LOGS_DIR / date_folder
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log files are named by date, not time (one per day)
    date_str = timestamp.strftime("%Y%m%d")
    return log_dir / f"{log_type}_{date_str}.log"


def cleanup_old_files(directory: Path, days_old: int = 30):
    """
    Clean up old files from a directory.
    
    Args:
        directory: Directory to clean
        days_old: Remove files older than this many days
    """
    import time
    
    if not directory.exists():
        return
    
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            file_time = file_path.stat().st_mtime
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    print(f"Removed old file: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")


def cleanup_old_data():
    """
    Run cleanup for all data directories based on retention policy.
    
    Retention policy:
    - Screenshots: 30 days
    - Debug files: 7 days
    - Logs: 90 days
    - Applications: Never (keep all)
    """
    print("Running data cleanup...")
    
    cleanup_old_files(SCREENSHOTS_DIR, days_old=30)
    cleanup_old_files(DEBUG_DIR, days_old=7)
    cleanup_old_files(LOGS_DIR, days_old=90)
    # Applications are not cleaned up automatically
    
    print("Cleanup complete.")


# Initialize directories on import
ensure_data_directories()
