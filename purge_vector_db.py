"""
Utility script to purge the Chroma vector database so you can start fresh before a new bulk import.

Usage:
    python purge_vector_db.py
"""
from storage.vector_db_manager import VectorDBManager


def main() -> None:
    vdb = VectorDBManager()
    name = vdb.collection.name
    # Drop the collection entirely
    vdb.persistent_client.delete_collection(name)
    # Recreate it so downstream code keeps working
    vdb.collection = vdb.persistent_client.get_or_create_collection(
        name=name,
        embedding_function=vdb.embedding_function,
        metadata={"description": "AI Use Case Catalogue"},
    )
    print("Collection reset:", vdb.collection.count())


if __name__ == "__main__":
    main()
