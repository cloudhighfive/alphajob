#!/usr/bin/env python3
"""
Cleanup old data files based on retention policy.

Usage:
    python scripts/cleanup_data.py [--dry-run]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.paths import cleanup_old_data, cleanup_old_files
from src.utils.paths import SCREENSHOTS_DIR, DEBUG_DIR, LOGS_DIR


def main():
    """Run data cleanup."""
    parser = argparse.ArgumentParser(description="Clean up old data files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--screenshots-days",
        type=int,
        default=30,
        help="Keep screenshots for this many days (default: 30)"
    )
    parser.add_argument(
        "--debug-days",
        type=int,
        default=7,
        help="Keep debug files for this many days (default: 7)"
    )
    parser.add_argument(
        "--logs-days",
        type=int,
        default=90,
        help="Keep logs for this many days (default: 90)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN - No files will be deleted\n")
    
    print("=" * 70)
    print("🧹 Data Cleanup Script")
    print("=" * 70)
    print(f"\nRetention Policy:")
    print(f"  Screenshots: {args.screenshots_days} days")
    print(f"  Debug files: {args.debug_days} days")
    print(f"  Log files: {args.logs_days} days")
    print(f"  Applications: Never deleted (keep all)")
    print()
    
    if args.dry_run:
        # For dry run, just show what would be cleaned
        import time
        from datetime import datetime, timedelta
        
        cutoff_dates = {
            "Screenshots": datetime.now() - timedelta(days=args.screenshots_days),
            "Debug files": datetime.now() - timedelta(days=args.debug_days),
            "Logs": datetime.now() - timedelta(days=args.logs_days),
        }
        
        dirs_to_check = [
            (SCREENSHOTS_DIR, args.screenshots_days, "Screenshots"),
            (DEBUG_DIR, args.debug_days, "Debug files"),
            (LOGS_DIR, args.logs_days, "Logs"),
        ]
        
        total_files = 0
        total_size = 0
        
        for directory, days, name in dirs_to_check:
            if not directory.exists():
                continue
            
            print(f"\n📁 Checking {name} in {directory}")
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            files_to_delete = []
            
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.name != ".gitkeep":
                    file_time = file_path.stat().st_mtime
                    if file_time < cutoff_time:
                        size = file_path.stat().st_size
                        files_to_delete.append((file_path, size))
            
            if files_to_delete:
                print(f"   Would delete {len(files_to_delete)} file(s):")
                for file_path, size in files_to_delete[:5]:  # Show first 5
                    print(f"     - {file_path.name} ({size:,} bytes)")
                if len(files_to_delete) > 5:
                    print(f"     ... and {len(files_to_delete) - 5} more")
                
                total_files += len(files_to_delete)
                total_size += sum(size for _, size in files_to_delete)
            else:
                print(f"   ✅ No files to delete")
        
        if total_files > 0:
            print(f"\n📊 Summary:")
            print(f"   Total files to delete: {total_files}")
            print(f"   Total size to free: {total_size / 1024 / 1024:.2f} MB")
            print(f"\n💡 Run without --dry-run to actually delete these files")
        else:
            print(f"\n✅ No files need to be cleaned up")
    
    else:
        # Actually run cleanup
        print("\n🧹 Running cleanup...")
        
        cleanup_old_files(SCREENSHOTS_DIR, days_old=args.screenshots_days)
        cleanup_old_files(DEBUG_DIR, days_old=args.debug_days)
        cleanup_old_files(LOGS_DIR, days_old=args.logs_days)
        
        print("\n✅ Cleanup complete!")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
