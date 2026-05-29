import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()
from backend.rag_engine import RAGEngine

try:
    print("Testing RAG Engine...")
    engine = RAGEngine(db_path="db")
    res = engine.query(user_query="hola", author="neville")
    print(res)
except Exception as e:
    traceback.print_exc()
