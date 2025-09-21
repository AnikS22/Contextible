#!/usr/bin/env python3
"""
Migration script to add embedding column to context_entries table.

This script:
1. Adds the embedding column to the database
2. Optionally generates embeddings for existing entries
"""

import logging
import sys
from pathlib import Path

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from contextvault.database import get_db_context
from contextvault.services.semantic_search import get_semantic_search_service
from contextvault.models.context import ContextEntry

logger = logging.getLogger(__name__)


def add_embedding_column():
    """Add the embedding column to the context_entries table."""
    try:
        with get_db_context() as db:
            # Check if column already exists
            result = db.execute(text("""
                SELECT COUNT(*) 
                FROM pragma_table_info('context_entries') 
                WHERE name = 'embedding'
            """))
            
            column_exists = result.scalar() > 0
            
            if column_exists:
                logger.info("Embedding column already exists")
                return True
            
            # Add the embedding column
            db.execute(text("""
                ALTER TABLE context_entries 
                ADD COLUMN embedding BLOB
            """))
            
            db.commit()
            logger.info("Successfully added embedding column to context_entries table")
            return True
            
    except Exception as e:
        logger.error(f"Failed to add embedding column: {e}")
        return False


def generate_embeddings_for_existing_entries():
    """Generate embeddings for all existing context entries."""
    try:
        semantic_service = get_semantic_search_service()
        
        if not semantic_service.is_available():
            logger.warning("Semantic search not available, skipping embedding generation")
            return False
        
        with get_db_context() as db:
            # Get all entries without embeddings
            entries = db.query(ContextEntry).filter(ContextEntry.embedding.is_(None)).all()
            
            if not entries:
                logger.info("No entries need embedding generation")
                return True
            
            logger.info(f"Generating embeddings for {len(entries)} entries...")
            
            # Generate embeddings in batches
            batch_size = 50
            updated_count = 0
            
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i + batch_size]
                
                # Extract content
                texts = [entry.content for entry in batch]
                
                # Generate embeddings
                embeddings = semantic_service.generate_embeddings_batch(texts)
                
                # Update entries
                for entry, embedding in zip(batch, embeddings):
                    if embedding is not None:
                        # Convert numpy array to bytes for storage
                        import pickle
                        entry.embedding = pickle.dumps(embedding)
                        updated_count += 1
                
                # Commit batch
                db.commit()
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(entries) + batch_size - 1)//batch_size}")
            
            logger.info(f"Successfully generated embeddings for {updated_count} entries")
            return True
            
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return False


def main():
    """Main migration function."""
    logging.basicConfig(level=logging.INFO)
    
    print("🔄 ContextVault Embedding Migration")
    print("=" * 50)
    
    # Step 1: Add embedding column
    print("\n1. Adding embedding column to database...")
    if not add_embedding_column():
        print("❌ Failed to add embedding column")
        return False
    
    print("✅ Embedding column added successfully")
    
    # Step 2: Ask user if they want to generate embeddings
    print("\n2. Generate embeddings for existing entries?")
    print("   This will create semantic search vectors for all existing context entries.")
    print("   This may take several minutes for large databases.")
    
    response = input("   Generate embeddings now? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n   Generating embeddings...")
        if generate_embeddings_for_existing_entries():
            print("✅ Embeddings generated successfully")
        else:
            print("❌ Failed to generate embeddings")
            print("   You can run this script again later to generate embeddings")
    else:
        print("⏭️  Skipping embedding generation")
        print("   Embeddings will be generated automatically as entries are accessed")
    
    print("\n🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("1. Install semantic search dependencies: pip install sentence-transformers torch")
    print("2. Restart ContextVault to enable semantic search")
    print("3. Test semantic search with: contextvault-cli context test-search \"your query\"")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
