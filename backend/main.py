import os
import base64
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

from backend.document_loader import load_document, chunk_text
from backend.vector_store import VectorStoreManager
from backend.rag_engine import RAGEngine
from backend.scheduler import start_scheduler, load_tasks

# Load environment variables (.env file)
load_dotenv()

# Initialize FastAPI App
app = FastAPI(title="Neville Goddard Library Public RAG API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
DB_DIR = os.path.join(BASE_DIR, "db")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Managers
vector_manager = VectorStoreManager(db_path=DB_DIR)
rag_engine = RAGEngine(db_path=DB_DIR)

# Models
class QueryRequest(BaseModel):
    query: str
    author: Optional[str] = "neville"
    top_k: Optional[int] = 8

# Startup event: Automatic Indexing of local documents in background thread
@app.on_event("startup")
def start_services():
    """
    Spawns background threads for document auto-indexing and task scheduling on startup.
    """
    import threading
    thread = threading.Thread(target=auto_index_documents, name="AutoIndexer")
    thread.daemon = True
    thread.start()
    
    # Start task scheduler
    start_scheduler()

def auto_index_documents():
    """
    Scans the local documents/ folder and indexes any new books.
    """
    print("\n" + "="*60)
    print(" INICIANDO INDEXACIÓN AUTOMÁTICA DE DOCUMENTOS ")
    print("="*60)
    
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("\nADVERTENCIA CRÍTICA:")
        print("La variable GEMINI_API_KEY no está configurada en tu entorno o archivo .env.")
        print("La indexación automática y las consultas de chat fallarán.")
        print("Por favor, crea un archivo '.env' con: GEMINI_API_KEY=tu_clave_aqui")
        print("="*60 + "\n")
        return

    # Check for files to index
    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)

    files = [f for f in os.listdir(DOCUMENTS_DIR) if os.path.isfile(os.path.join(DOCUMENTS_DIR, f))]
    supported_extensions = ['.pdf', '.epub', '.txt', '.md', '.markdown']
    files = [f for f in files if os.path.splitext(f.lower())[1] in supported_extensions]

    if not files:
        print(f"\nNo se encontraron libros en la carpeta '{DOCUMENTS_DIR}/'.")
        print("Coloca tus archivos PDF, EPUB o TXT allí para que sean indexados.")
        print("="*60 + "\n")
        return

    try:
        indexed_docs = vector_manager.get_indexed_documents()
    except Exception as e:
        print(f"\nError al conectar con la base de datos vectorial (ChromaDB): {e}")
        print("="*60 + "\n")
        return

    print(f"Documentos ya indexados anteriormente: {len(indexed_docs)}")
    print(f"Documentos detectados físicamente: {len(files)}")
    
    new_files_indexed = 0
    for filename in files:
        if filename in indexed_docs:
            print(f" -> '{filename}' ya se encuentra indexado. [OK]")
            continue
            
        print(f" -> Indexando nuevo libro: '{filename}'...")
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        
        try:
            # Parse document
            raw_docs = load_document(file_path)
            if not raw_docs:
                print(f"    [!] Error: No se pudo extraer texto de '{filename}'")
                continue
                
            # Split into chunks
            chunks = chunk_text(raw_docs, chunk_size=1000, chunk_overlap=200)
            
            # Store in ChromaDB
            vector_manager.add_chunks(chunks, api_key=key)
            print(f"    [+] Indexado con éxito ({len(chunks)} fragmentos).")
            new_files_indexed += 1
            
            # Cooldown sleep to prevent rate limit issues between documents
            import time
            time.sleep(5)
        except Exception as e:
            print(f"    [!] Error procesando '{filename}': {e}")
            
    print("="*60)
    print(f" PROCESO COMPLETADO: {new_files_indexed} libros nuevos indexados.")
    print("="*60 + "\n")

# API Endpoints
@app.get("/api/documents")
def list_documents():
    """
    Returns list of all indexed documents in the database.
    Public endpoint.
    """
    try:
        docs = vector_manager.get_indexed_documents()
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar documentos: {str(e)}")

class TaskRequest(BaseModel):
    message: str
    scheduled_time: str
    platform: str
    target_number: Optional[str] = None

@app.get("/api/tasks")
def list_tasks():
    try:
        tasks = load_tasks()
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar tareas: {str(e)}")

@app.post("/api/tasks")
def create_task(req: TaskRequest):
    try:
        from backend.scheduler import schedule_task
        task = schedule_task(req.message, req.scheduled_time, req.platform, req.target_number)
        return {"ok": True, "task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al programar tarea: {str(e)}")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        from backend.scheduler import save_tasks
        tasks = load_tasks()
        tasks = [t for t in tasks if t["id"] != task_id]
        save_tasks(tasks)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Recibe un archivo de audio (webm/mp4/ogg/wav) y usa Gemini para transcribirlo.
    Funciona como fallback cuando el browser no soporta SpeechRecognition nativo
    (ej: Chrome en iOS).
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada")

    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio vacío")

        # Detectar mime type
        content_type = audio.content_type or "audio/webm"
        # Algunos browsers envían audio/webm;codecs=opus → normalizar
        mime_type = content_type.split(";")[0].strip()
        if mime_type not in ("audio/webm", "audio/ogg", "audio/mp4", "audio/wav", "audio/mpeg"):
            mime_type = "audio/webm"

        # Codificar en base64 para Gemini inline
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        genai.configure(api_key=key)
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        response = model.generate_content([
            "Transcribí exactamente lo que se dice en este audio en español argentino. "
            "Devolvé ÚNICAMENTE la transcripción, sin ningún texto adicional, sin comillas, sin explicaciones.",
            {"inline_data": {"mime_type": mime_type, "data": audio_b64}}
        ])

        transcript = response.text.strip() if response.text else ""
        if not transcript:
            raise HTTPException(status_code=422, detail="No se pudo transcribir el audio")

        return {"transcript": transcript}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribiendo: {str(e)}")


@app.post("/api/query")

def run_query(request: QueryRequest):
    """
    RAG chat endpoint. Takes a query, retrieves chunks and answers it using Gemini API.
    Public endpoint.
    """
    load_dotenv(override=True)
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise HTTPException(
            status_code=500, 
            detail="La variable GEMINI_API_KEY no está configurada en el servidor (archivo .env)."
        )
        
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía.")
        
    try:
        response = rag_engine.query(
            user_query=request.query, 
            author=request.author,
            api_key=key, 
            top_k=request.top_k
        )
        return response
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Has excedido la cuota de consultas diarias de la API de Gemini (Free Tier tiene un límite de 20 preguntas al día). Por favor, intenta de nuevo más tarde o configura una clave de API con facturación habilitada en tu archivo .env."
            )
        raise HTTPException(status_code=500, detail=f"Error en el motor RAG: {error_msg}")


# Mount static frontend files
@app.get("/")
def get_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend no inicializado. Crea frontend/index.html"}

app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
