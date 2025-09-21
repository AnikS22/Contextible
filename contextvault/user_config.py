#!/usr/bin/env python3
"""
User Configuration Template for Contextible

Copy this file to user_config_local.py and customize the paths for your system.
This ensures no hardcoded personal paths are in the main codebase.
"""

import os
from pathlib import Path

# User-specific configuration
# Copy this file to user_config_local.py and customize these values

# Project root directory (where you store your projects)
PROJECT_ROOT = os.path.expanduser("~/Projects")  # Default: ~/Projects

# Contextible installation directory
CONTEXTIBLE_ROOT = os.path.join(PROJECT_ROOT, "contextible")

# ContextVault specific directory
CONTEXTVAULT_ROOT = os.path.join(CONTEXTIBLE_ROOT, "contextvault")

# Google Drive path (if using Google Drive for Desktop)
GOOGLE_DRIVE_PATH = os.path.expanduser("~/Google Drive")  # Default: ~/Google Drive

# Other common paths
DESKTOP_PATH = os.path.expanduser("~/Desktop")
DOCUMENTS_PATH = os.path.expanduser("~/Documents")
DOWNLOADS_PATH = os.path.expanduser("~/Downloads")

# Development paths
DEV_ROOT = os.path.expanduser("~/Development")  # Alternative to PROJECT_ROOT

def get_user_paths():
    """Get all user-specific paths as a dictionary."""
    return {
        "project_root": PROJECT_ROOT,
        "contextible_root": CONTEXTIBLE_ROOT,
        "contextvault_root": CONTEXTVAULT_ROOT,
        "google_drive_path": GOOGLE_DRIVE_PATH,
        "desktop_path": DESKTOP_PATH,
        "documents_path": DOCUMENTS_PATH,
        "downloads_path": DOWNLOADS_PATH,
        "dev_root": DEV_ROOT,
    }

def get_custom_path(path_type: str, default: str = None):
    """Get a custom path, checking environment variables first."""
    env_var = f"CONTEXTIBLE_{path_type.upper()}"
    return os.environ.get(env_var, default or get_user_paths().get(path_type, ""))

# Example usage:
# from user_config import get_user_paths, get_custom_path
# paths = get_user_paths()
# custom_path = get_custom_path("project_root", "~/MyProjects")
