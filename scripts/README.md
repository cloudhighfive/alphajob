# Scripts Directory

Utility scripts for project maintenance and data management.

## Available Scripts

### cleanup_data.py

Automated cleanup script for removing old data files based on retention policy.

**Usage:**

```bash
# Dry run (see what would be deleted)
python scripts/cleanup_data.py --dry-run

# Actually run cleanup with default retention
python scripts/cleanup_data.py

# Custom retention periods
python scripts/cleanup_data.py --screenshots-days 60 --debug-days 14 --logs-days 180
```

**Options:**

- `--dry-run` - Show what would be deleted without actually deleting
- `--screenshots-days N` - Keep screenshots for N days (default: 30)
- `--debug-days N` - Keep debug files for N days (default: 7)
- `--logs-days N` - Keep logs for N days (default: 90)

**Default Retention Policy:**

| Data Type | Retention Period | Reason |
|-----------|-----------------|---------|
| Screenshots | 30 days | Visual verification |
| Debug files | 7 days | Troubleshooting only |
| Logs | 90 days | Compliance/auditing |
| Applications | Forever | Historical record |

**Scheduling:**

Set up a cron job to run cleanup automatically:

```bash
# Run cleanup every day at 3 AM
0 3 * * * cd /path/to/project && python scripts/cleanup_data.py
```

Or add to your crontab:

```bash
crontab -e
```

Then add the line above.

## Future Scripts

Additional scripts that could be added:

- `backup_applications.py` - Backup application data to cloud storage
- `generate_report.py` - Generate statistics report from application data
- `migrate_data.py` - Migrate data from old structure to new structure
- `validate_data.py` - Validate integrity of application data files
- `export_csv.py` - Export application data to CSV for analysis
