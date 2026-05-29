import os
import sys
from dotenv import load_dotenv

# Add current folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.document_loader import load_document, chunk_text
from backend.vector_store import VectorStoreManager

def main():
    load_dotenv()
    key = os.environ.get("GEMINI_API_KEY")
    print(f"API Key loaded from environment: {bool(key)}")
    if not key:
        print("No API Key found!")
        return

    vector_manager = VectorStoreManager(db_path="db")
    DOCUMENTS_DIR = "documents"
    
    try:
        indexed = vector_manager.get_indexed_documents()
        print(f"Already indexed documents: {indexed}")
    except Exception as e:
        print(f"Error getting indexed documents: {e}")
        indexed = []

    for author_dir in os.listdir(DOCUMENTS_DIR):
        author_path = os.path.join(DOCUMENTS_DIR, author_dir)
        if not os.path.isdir(author_path):
            continue
            
        files = [f for f in os.listdir(author_path) if os.path.isfile(os.path.join(author_path, f))]
        print(f"Files found for author '{author_dir}': {files}")
        
        for filename in files:
            if filename in indexed:
                print(f"'{filename}' is already indexed.")
                continue
                
            print(f"Indexing '{filename}' for author '{author_dir}'...")
            file_path = os.path.join(author_path, filename)
            try:
                raw_docs = load_document(file_path)
                print(f"Loaded {len(raw_docs)} sections from document.")
                chunks = chunk_text(raw_docs)
                
                # Add author metadata to every chunk
                for chunk in chunks:
                    chunk["metadata"]["author"] = author_dir
                    
                print(f"Generated {len(chunks)} chunks.")
                vector_manager.add_chunks(chunks, api_key=key)
                print("Successfully added chunks to ChromaDB!")
            except Exception as e:
                print(f"Error indexing '{filename}': {e}")

if __name__ == "__main__":
    main()
