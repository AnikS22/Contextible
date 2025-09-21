#!/usr/bin/env python3
"""
Clean up debug code from the codebase
"""

import os
import re
from pathlib import Path

def cleanup_file(file_path):
    """Remove debug print statements from a file."""
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove debug print statements
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that contain debug print statements
        if any(debug_pattern in line for debug_pattern in [
            '[PROXY DEBUG]',
            '[INJECTION DEBUG]',
            '[CONTEXT RETRIEVAL DEBUG]',
            '[PERMISSION DEBUG]',
            '[INJECTION ERROR]',
            '[CONTEXT RETRIEVAL ERROR]',
            '[PERMISSION ERROR]'
        ]):
            continue
        cleaned_lines.append(line)
    
    # Write cleaned content back
    cleaned_content = '\n'.join(cleaned_lines)
    with open(file_path, 'w') as f:
        f.write(cleaned_content)
    
    print(f"✅ Cleaned up debug code from {file_path}")

def main():
    """Clean up debug code from all relevant files."""
    print("🧹 Cleaning up debug code...")
    
    files_to_clean = [
        "contextvault/integrations/base.py",
        "contextvault/integrations/ollama.py", 
        "contextvault/services/context_retrieval.py",
        "contextvault/services/permissions.py"
    ]
    
    for file_path in files_to_clean:
        cleanup_file(file_path)
    
    print("✅ Debug code cleanup completed!")

if __name__ == "__main__":
    main()
