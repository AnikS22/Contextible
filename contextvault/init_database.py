#!/usr/bin/env python3
"""
Database Initialization Script for Contextible

Run this script to initialize the database with all required tables.
This is automatically called during setup, but can be run manually if needed.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def init_database():
    """Initialize the Contextible database."""
    try:
        print("🗄️ Initializing Contextible Database...")
        
        # Import database functions
        from contextvault.database import init_database, create_tables, check_database_connection
        
        # Initialize database
        print("📁 Setting up database connection...")
        init_database()
        
        # Create tables
        print("🏗️ Creating database tables...")
        create_tables()
        
        # Test connection
        print("🔍 Testing database connection...")
        connection_info = check_database_connection()
        print(f"✅ Database connected: {connection_info}")
        
        print("\n🎉 Database initialization complete!")
        print("✅ All tables created successfully")
        print("✅ Ready to store context entries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the contextvault directory")
        print("2. Check that all dependencies are installed: pip install -r requirements.txt")
        print("3. Try running: python -c 'import contextvault; print(\"Dependencies OK\")'")
        return False

def verify_tables():
    """Verify that all required tables exist."""
    try:
        from contextvault.database import get_db_session
        from contextvault.models.context import ContextEntry
        from contextvault.models.sessions import SessionModel
        from contextvault.models.permissions import Permission
        
        print("\n🔍 Verifying database tables...")
        
        with get_db_session() as db:
            # Try to query each table
            db.query(ContextEntry).first()
            print("✅ context_entries table exists")
            
            db.query(SessionModel).first()
            print("✅ sessions table exists")
            
            db.query(Permission).first()
            print("✅ permissions table exists")
        
        print("✅ All tables verified!")
        return True
        
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Contextible Database Setup")
    print("=" * 40)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        sys.exit(1)
    
    print("\n🎯 Next Steps:")
    print("1. Run: python contextible.py")
    print("2. Try: add \"My name is John and I'm a developer\"")
    print("3. Try: list")
    print("4. Start the proxy: python scripts/ollama_proxy.py")
    
    print("\n✅ Database setup complete! Contextible is ready to use.")

if __name__ == "__main__":
    main()
