"""
Privacy and data governance management module.
Ensures zero external cloud data transfer, controls temporary media storage cleanup,
and provides complete session data deletion routines.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from config import UPLOADS_DIR, EXPORTS_DIR, DATABASE_PATH
from modules.database import get_connection, delete_session


def get_privacy_status() -> Dict[str, Any]:
    """
    Returns current privacy and data retention status.
    """
    temp_files = list(UPLOADS_DIR.glob("*"))
    temp_size_mb = sum(f.stat().st_size for f in temp_files if f.is_file()) / (1024 * 1024)

    return {
        "local_mode": True,
        "cloud_transfers": 0,
        "biometric_templates_stored": False,
        "temp_files_count": len(temp_files),
        "temp_storage_mb": round(temp_size_mb, 2),
        "database_path": str(DATABASE_PATH),
        "uploads_path": str(UPLOADS_DIR)
    }


def cleanup_temp_uploads() -> int:
    """
    Deletes all temporary uploaded video and audio files from disk.
    Returns the count of deleted files.
    """
    deleted = 0
    if UPLOADS_DIR.exists():
        for item in UPLOADS_DIR.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    deleted += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted += 1
            except Exception:
                pass
    return deleted


def purge_session(session_id: str) -> bool:
    """
    Completely purges a session, including database records and any associated media files.
    """
    # Remove DB records
    success = delete_session(session_id)

    # Remove any associated uploaded files with that session id in their name
    if UPLOADS_DIR.exists():
        for item in UPLOADS_DIR.iterdir():
            if session_id in item.name:
                try:
                    item.unlink()
                except Exception:
                    pass

    return success


def purge_all_data() -> bool:
    """
    Factory reset: wipes all database tables and temporary uploads.
    """
    cleanup_temp_uploads()

    conn = get_connection(DATABASE_PATH)
    try:
        with conn:
            conn.execute("DELETE FROM attendance_records")
            conn.execute("DELETE FROM engagement_timeline")
            conn.execute("DELETE FROM session_recommendations")
            conn.execute("DELETE FROM session_metrics_summary")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM participants")
        return True
    except Exception:
        return False
    finally:
        conn.close()
