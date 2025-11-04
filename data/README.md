# Data Directory Structure

This directory contains application runtime data, organized by type.

## Directory Structure

```
data/
├── screenshots/          # Application screenshots
│   ├── pre_submit/      # Screenshots before submission
│   └── post_submit/     # Screenshots after submission
├── applications/        # Submitted application data
│   └── YYYY-MM-DD/     # Organized by date
├── debug/              # Debug artifacts
│   ├── form_html/      # HTML dumps for debugging
│   └── form_debug/     # Debug screenshots
└── logs/               # Application logs
    └── YYYY-MM-DD/     # Log files organized by date
```

## File Naming Conventions

### Screenshots
- **Pre-submit**: `pre_submit_YYYYMMDD_HHMMSS.png`
- **Post-submit**: `post_submit_YYYYMMDD_HHMMSS.png`
- **Application**: `application_screenshot_YYYYMMDD_HHMMSS.png`

### Applications
- **Filled data**: `filled_application_YYYYMMDD_HHMMSS.json`
- **Organized by date**: `data/applications/2025-11-03/filled_application_20251103_105621.json`

### Debug Files
- **Form HTML**: `form_html_debug_YYYYMMDD_HHMMSS.html`
- **Form debug screenshot**: `form_debug_TIMESTAMP.png`

### Logs
- **Application logs**: `app_YYYYMMDD.log`
- **Error logs**: `error_YYYYMMDD.log`

## Retention Policy

- **Screenshots**: Keep for 30 days
- **Applications**: Keep permanently (or until archived)
- **Debug files**: Keep for 7 days
- **Logs**: Keep for 90 days

## Gitignore

All files in this directory are gitignored by default to protect:
- Personal information in screenshots
- Sensitive application data
- Debug information
- Log files

## Automated Cleanup

Consider implementing automated cleanup scripts:

```bash
# Clean old debug files (older than 7 days)
find data/debug -type f -mtime +7 -delete

# Clean old screenshots (older than 30 days)
find data/screenshots -type f -mtime +30 -delete

# Archive old logs (older than 90 days)
find data/logs -type f -mtime +90 -exec gzip {} \;
```

## Usage in Code

```python
from pathlib import Path
from datetime import datetime

# Base data directory
DATA_DIR = Path("data")

# Create timestamped filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save screenshot
screenshot_path = DATA_DIR / "screenshots" / "pre_submit" / f"pre_submit_{timestamp}.png"
screenshot_path.parent.mkdir(parents=True, exist_ok=True)

# Save application
date_folder = datetime.now().strftime("%Y-%m-%d")
app_path = DATA_DIR / "applications" / date_folder / f"filled_application_{timestamp}.json"
app_path.parent.mkdir(parents=True, exist_ok=True)

# Save debug info
debug_path = DATA_DIR / "debug" / "form_html" / f"form_html_debug_{timestamp}.html"
debug_path.parent.mkdir(parents=True, exist_ok=True)

# Save logs
log_path = DATA_DIR / "logs" / f"app_{datetime.now().strftime('%Y%m%d')}.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
```
