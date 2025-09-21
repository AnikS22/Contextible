#!/usr/bin/env python3
"""Import/export utilities for ContextVault."""

import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.services import vault_service
from contextvault.models import ContextType
from contextvault.database import check_database_connection


def export_to_json(output_file: str, filters: Optional[Dict[str, Any]] = None) -> bool:
    """Export context data to JSON format."""
    try:
        print(f"📤 Exporting context data to {output_file}...")
        
        export_data = vault_service.export_context(filters=filters, format="json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        total_entries = export_data["metadata"]["total_entries"]
        print(f"✅ Successfully exported {total_entries} entries to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def export_to_csv(output_file: str, filters: Optional[Dict[str, Any]] = None) -> bool:
    """Export context data to CSV format."""
    try:
        print(f"📤 Exporting context data to {output_file}...")
        
        # Get context entries
        entries, total = vault_service.get_context(
            filters=filters or {},
            limit=10000,  # Large limit for export
        )
        
        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'id', 'content', 'context_type', 'source', 'tags', 
                'created_at', 'updated_at', 'access_count', 'user_id'
            ])
            
            # Write entries
            for entry in entries:
                writer.writerow([
                    entry.id,
                    entry.content,
                    entry.context_type.value,
                    entry.source or '',
                    ','.join(entry.tags) if entry.tags else '',
                    entry.created_at.isoformat() if entry.created_at else '',
                    entry.updated_at.isoformat() if entry.updated_at else '',
                    entry.access_count or 0,
                    entry.user_id or '',
                ])
        
        print(f"✅ Successfully exported {len(entries)} entries to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def import_from_json(input_file: str, skip_duplicates: bool = True) -> bool:
    """Import context data from JSON format."""
    try:
        print(f"📥 Importing context data from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        if "entries" not in import_data:
            print("❌ Invalid import file format - missing 'entries' field")
            return False
        
        entries = import_data["entries"]
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, entry_data in enumerate(entries):
            try:
                # Check for required fields
                if "content" not in entry_data:
                    print(f"⚠️  Skipping entry {i+1}: missing content")
                    skipped_count += 1
                    continue
                
                # Check for duplicates if requested
                if skip_duplicates:
                    existing_entries, _ = vault_service.get_context(
                        filters={"search": entry_data["content"][:50]},
                        limit=5,
                    )
                    
                    # Simple duplicate check based on content
                    for existing in existing_entries:
                        if existing.content.strip() == entry_data["content"].strip():
                            print(f"⚠️  Skipping entry {i+1}: duplicate content")
                            skipped_count += 1
                            continue
                
                # Import the entry
                vault_service.save_context(
                    content=entry_data["content"],
                    context_type=ContextType(entry_data.get("context_type", "text")),
                    source=entry_data.get("source"),
                    tags=entry_data.get("tags"),
                    metadata=entry_data.get("metadata"),
                    user_id=entry_data.get("user_id"),
                )
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"   Imported {imported_count} entries...")
                
            except Exception as e:
                print(f"⚠️  Error importing entry {i+1}: {e}")
                error_count += 1
        
        print(f"✅ Import completed:")
        print(f"   Imported: {imported_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Errors: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def import_from_csv(input_file: str, skip_duplicates: bool = True) -> bool:
    """Import context data from CSV format."""
    try:
        print(f"📥 Importing context data from {input_file}...")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                try:
                    content = row.get('content', '').strip()
                    if not content:
                        print(f"⚠️  Skipping row {i+1}: empty content")
                        skipped_count += 1
                        continue
                    
                    # Check for duplicates if requested
                    if skip_duplicates:
                        existing_entries, _ = vault_service.get_context(
                            filters={"search": content[:50]},
                            limit=5,
                        )
                        
                        for existing in existing_entries:
                            if existing.content.strip() == content:
                                print(f"⚠️  Skipping row {i+1}: duplicate content")
                                skipped_count += 1
                                continue
                    
                    # Parse tags
                    tags = []
                    if row.get('tags'):
                        tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                    
                    # Import the entry
                    vault_service.save_context(
                        content=content,
                        context_type=ContextType(row.get('context_type', 'text')),
                        source=row.get('source') or None,
                        tags=tags if tags else None,
                        user_id=row.get('user_id') or None,
                    )
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        print(f"   Imported {imported_count} entries...")
                
                except Exception as e:
                    print(f"⚠️  Error importing row {i+1}: {e}")
                    error_count += 1
        
        print(f"✅ Import completed:")
        print(f"   Imported: {imported_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Errors: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def main():
    """Main function for import/export utility."""
    parser = argparse.ArgumentParser(
        description="Import/export utility for ContextVault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all data to JSON
  python import_export.py export data.json

  # Export to CSV
  python import_export.py export data.csv --format csv

  # Import from JSON
  python import_export.py import data.json

  # Import from CSV
  python import_export.py import data.csv --format csv

  # Export with filters
  python import_export.py export recent.json --context-type preference --tags coding
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export context data')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                              help='Export format (default: json)')
    export_parser.add_argument('--context-type', 
                              choices=['text', 'file', 'event', 'preference', 'note'],
                              help='Filter by context type')
    export_parser.add_argument('--tags', help='Filter by tags (comma-separated)')
    export_parser.add_argument('--source', help='Filter by source pattern')
    export_parser.add_argument('--since', help='Filter entries since date (YYYY-MM-DD)')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import context data')
    import_parser.add_argument('input_file', help='Input file path')
    import_parser.add_argument('--format', choices=['json', 'csv'], 
                              help='Import format (auto-detected if not specified)')
    import_parser.add_argument('--allow-duplicates', action='store_true',
                              help='Allow duplicate entries (default: skip duplicates)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot connect to database. Check your configuration.")
        return 1
    
    if args.command == 'export':
        # Build filters
        filters = {}
        
        if args.context_type:
            filters['context_types'] = [ContextType(args.context_type)]
        
        if args.tags:
            filters['tags'] = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
        
        if args.source:
            filters['source'] = args.source
        
        if args.since:
            try:
                from datetime import datetime
                filters['since'] = datetime.fromisoformat(args.since)
            except ValueError:
                print(f"❌ Invalid date format: {args.since}. Use YYYY-MM-DD")
                return 1
        
        # Determine format from file extension if not specified
        if args.format == 'json' or args.output_file.endswith('.json'):
            success = export_to_json(args.output_file, filters)
        elif args.format == 'csv' or args.output_file.endswith('.csv'):
            success = export_to_csv(args.output_file, filters)
        else:
            print("❌ Could not determine format. Use --format or use .json/.csv extension")
            return 1
        
        return 0 if success else 1
    
    elif args.command == 'import':
        # Determine format
        format_type = args.format
        if not format_type:
            if args.input_file.endswith('.json'):
                format_type = 'json'
            elif args.input_file.endswith('.csv'):
                format_type = 'csv'
            else:
                print("❌ Could not determine format. Use --format or use .json/.csv extension")
                return 1
        
        skip_duplicates = not args.allow_duplicates
        
        if format_type == 'json':
            success = import_from_json(args.input_file, skip_duplicates)
        elif format_type == 'csv':
            success = import_from_csv(args.input_file, skip_duplicates)
        else:
            print(f"❌ Unsupported format: {format_type}")
            return 1
        
        return 0 if success else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
