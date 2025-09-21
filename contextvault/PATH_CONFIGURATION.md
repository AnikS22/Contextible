# Path Configuration Guide

This guide explains how to configure Contextible for your specific system paths without hardcoding personal information.

## Quick Setup

1. **Copy the configuration template:**
   ```bash
   cp user_config_local.py.example user_config_local.py
   ```

2. **Edit your paths:**
   ```bash
   nano user_config_local.py
   ```

3. **Customize the paths for your system:**
   ```python
   # Example for user "johndoe"
   PROJECT_ROOT = os.path.expanduser("~/Projects")
   GOOGLE_DRIVE_PATH = os.path.expanduser("~/Google Drive")
   ```

## Configuration Options

### Method 1: Configuration File (Recommended)

Edit `user_config_local.py` with your actual paths:

```python
# Your project root directory
PROJECT_ROOT = os.path.expanduser("~/MyProjects")

# Your Google Drive path (if using Google Drive for Desktop)
GOOGLE_DRIVE_PATH = os.path.expanduser("~/MyDrive")

# Other paths
DESKTOP_PATH = os.path.expanduser("~/Desktop")
DOCUMENTS_PATH = os.path.expanduser("~/Documents")
```

### Method 2: Environment Variables

Set environment variables in your shell:

```bash
# In ~/.bashrc, ~/.zshrc, or ~/.profile
export CONTEXTIBLE_PROJECT_ROOT="~/MyProjects"
export CONTEXTIBLE_GOOGLE_DRIVE_PATH="~/MyDrive"
export CONTEXTIBLE_CONTEXTVAULT_ROOT="~/MyProjects/contextible/contextvault"
```

### Method 3: Default Paths

If no configuration is provided, Contextible uses these defaults:

- **Project Root**: `~/Projects`
- **Google Drive**: `~/Google Drive`
- **ContextVault**: `~/Projects/contextible/contextvault`

## Common Path Configurations

### Standard User
```python
PROJECT_ROOT = os.path.expanduser("~/Projects")
GOOGLE_DRIVE_PATH = os.path.expanduser("~/Google Drive")
```

### Developer with Custom Structure
```python
PROJECT_ROOT = os.path.expanduser("~/Development")
GOOGLE_DRIVE_PATH = os.path.expanduser("~/Cloud/Google Drive")
```

### Windows User (WSL)
```python
PROJECT_ROOT = os.path.expanduser("~/projects")
GOOGLE_DRIVE_PATH = os.path.expanduser("/mnt/c/Users/YourName/Google Drive")
```

### macOS with Custom Drive
```python
PROJECT_ROOT = os.path.expanduser("~/Desktop/Projects")
GOOGLE_DRIVE_PATH = os.path.expanduser("~/OneDrive")
```

## Verification

Test your configuration:

```bash
python -c "from user_config_local import get_user_paths; print(get_user_paths())"
```

Expected output:
```
{
    'project_root': '/Users/yourname/Projects',
    'contextible_root': '/Users/yourname/Projects/contextible',
    'contextvault_root': '/Users/yourname/Projects/contextible/contextvault',
    'google_drive_path': '/Users/yourname/Google Drive',
    ...
}
```

## Security Notes

- ✅ `user_config_local.py` is excluded from git (your personal paths stay private)
- ✅ The example file shows safe defaults
- ✅ Environment variables provide additional security
- ✅ No personal paths are hardcoded in the main codebase

## Troubleshooting

### Path Not Found
If you get "path not found" errors:

1. Check your configuration file exists: `ls user_config_local.py`
2. Verify paths exist: `ls ~/YourConfiguredPath`
3. Check environment variables: `echo $CONTEXTIBLE_PROJECT_ROOT`

### Permission Denied
If you get permission errors:

```bash
# Make sure the script is executable
chmod +x user_config_local.py

# Check directory permissions
ls -la ~/YourConfiguredPath
```

### Import Error
If you get import errors:

1. Make sure you copied the example file: `cp user_config_local.py.example user_config_local.py`
2. Check Python path: `python -c "import sys; print(sys.path)"`
3. Verify file location: `pwd` (should be in contextvault directory)

## Advanced Configuration

### Custom Environment Variables
You can override any path using environment variables:

```bash
# Override specific paths
export CONTEXTIBLE_PROJECT_ROOT="~/CustomProjects"
export CONTEXTIBLE_GOOGLE_DRIVE_PATH="~/CustomDrive"

# Run Contextible with custom paths
python contextible.py
```

### Multiple Configurations
Create different configuration files for different setups:

```bash
# Development setup
cp user_config_local.py.example user_config_dev.py

# Production setup  
cp user_config_local.py.example user_config_prod.py

# Use specific configuration
CONTEXTIBLE_CONFIG=dev python contextible.py
```

This ensures your personal paths are never committed to the repository while maintaining full functionality!
