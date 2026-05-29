import os
import time
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
import google.generativeai as genai

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom ChromaDB Embedding Function that uses Google Gemini's
    text-embedding-004 model to avoid downloading local models.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        
    def __call__(self, input: Documents) -> Embeddings:
        if not self.api_key:
            raise ValueError("API Key de Gemini no configurada.")
        
        # Debug input type and size
        if isinstance(input, list):
            print(f"\n[DEBUG] Generando embeddings para lote de {len(input)} textos.")
        else:
            print(f"\n[DEBUG] Generando embedding para texto individual de longitud {len(input)}.")
            input = [input] # Ensure it's a list for consistency
            
        genai.configure(api_key=self.api_key)
        
        max_retries = 6
        base_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Call Gemini embedding API
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=input,
                    task_type="retrieval_document"
                )
                embeddings = response.get('embedding', [])
                
                # If it's a single embedding (list of floats) instead of list of lists, wrap it
                if embeddings and not isinstance(embeddings[0], list):
                    return [embeddings]
                return embeddings
            except Exception as e:
                err_msg = str(e)
                is_rate_limit = any(term in err_msg.lower() for term in ["429", "quota", "rate limit", "resource exhausted"])
                
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)
                    print(f"\n[!] Límite de cuota (429) alcanzado al generar embeddings. Reintentando en {sleep_time} segundos... (Intento {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    print(f"Error generando embeddings: {e}")
                    raise e

class VectorStoreManager:
    def __init__(self, db_path="db", collection_name="neville_goddard"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.db_path)
        
    def _get_api_key(self, api_key=None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        return key

    def get_collection(self, api_key=None):
        # Use local ONNX model to avoid API key and rate limit issues
        from chromadb.utils import embedding_functions
        embedding_function = embedding_functions.ONNXMiniLM_L6_V2()
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_function
        )

    def add_chunks(self, chunks, api_key=None):
        """
        Adds text chunks to the Chroma DB vector store.
        """
        if not chunks:
            return
            
        collection = self.get_collection(api_key)
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            text = chunk["text"]
            meta = chunk["metadata"]
            
            # Create a unique ID for each chunk
            chunk_id = f"{meta['source']}_p{meta['page']}_ch{meta['chunk_index']}"
            
            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(meta)
            
        # Add to collection in batches if very large to respect API rate limits
        batch_size = 250
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
            # Add a small pause between batches to avoid hitting rate limits
            time.sleep(2)

    def search_similarity(self, query, top_k=5, api_key=None, author="neville"):
        """
        Performs semantic similarity search, filtered by author.
        Uses local ONNX embedding function automatically via ChromaDB.
        """
        collection = self.get_collection(api_key)
        
        # Add where clause for author filtering
        where_clause = {"author": author} if author else None
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            
            for doc, meta, dist in zip(docs, metas, dists):
                # Convert distance to score (cosine distance is between 0 and 2 for normalized vectors)
                score = round(1 - (dist / 2.0), 4) if dist is not None else 0.0
                formatted_results.append({
                    "text": doc,
                    "metadata": meta,
                    "score": score
                })
                
        return formatted_results

    def delete_document(self, filename):
        """
        Deletes all chunks associated with a specific filename.
        Uses get_collection without creating one to avoid conflicts.
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            collection.delete(where={"source": filename})
            return True
        except Exception as e:
            # If collection doesn't exist, we don't need to delete anything
            print(f"Error al eliminar o colección inexistente al borrar {filename}: {e}")
            return False

    def get_indexed_documents(self):
        """
        Lists all unique source filenames indexed in the database.
        Uses get_collection without creating one to avoid conflicts.
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            results = collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            sources = set()
            for meta in metadatas:
                if meta and "source" in meta:
                    sources.add(meta["source"])
            return list(sources)
        except Exception as e:
            # If collection doesn't exist yet, return empty list
            print(f"No se encontró colección o error al listar documentos: {e}")
            return []
