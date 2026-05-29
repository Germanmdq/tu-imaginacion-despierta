import os
import json
from supabase_client import supabase

JSON_DIR = "../json_extraidos"
AUDIO_DIR = os.path.join(JSON_DIR, "audios")
BUCKET_NAME = "audios"

def setup_bucket():
    """Crea el bucket de audios si no existe y lo hace público."""
    buckets = supabase.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    
    if BUCKET_NAME not in bucket_names:
        print(f"Creando bucket '{BUCKET_NAME}'...")
        # En la API de python se pasa un dicc con public=True
        supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
        print("Bucket creado exitosamente.")
    else:
        print(f"Bucket '{BUCKET_NAME}' ya existe.")

def seed_database():
    print("Iniciando subida de datos a Supabase...")
    setup_bucket()
    
    for filename in os.listdir(JSON_DIR):
        if not filename.endswith(".json"):
            continue
            
        json_path = os.path.join(JSON_DIR, filename)
        audio_name = filename.replace(".json", ".mp3")
        audio_path = os.path.join(AUDIO_DIR, audio_name)
        
        # 1. Leer JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Verificar si la conferencia ya existe en la DB
        titulo = data.get("titulo", "Sin Título")
        print(f"\nProcesando: {titulo}")
        
        existing = supabase.table("library").select("id").eq("titulo", titulo).execute()
        if len(existing.data) > 0:
            print(f"-> Ya existe en la base de datos, saltando...")
            continue
            
        audio_url = None
        
        # 2. Subir Audio a Supabase Storage
        if os.path.exists(audio_path):
            print(f"-> Subiendo audio {audio_name} a Storage...")
            try:
                with open(audio_path, 'rb') as af:
                    # En storage3 de supabase-py, es mejor pasar los bytes
                    supabase.storage.from_(BUCKET_NAME).upload(audio_name, af.read(), {"content-type": "audio/mpeg"})
            except Exception as e:
                # Si el archivo ya existe lanza una excepción, ignoramos
                print(f"   (Nota: el audio podría ya estar subido: {e})")
                
            # Obtener URL pública
            audio_url = supabase.storage.from_(BUCKET_NAME).get_public_url(audio_name)
            print(f"-> URL del audio obtenida: {audio_url}")
        else:
            print(f"-> ADVERTENCIA: No se encontró archivo de audio {audio_name}")
            
        # 3. Subir fila a la tabla library
        print("-> Insertando documento en la tabla 'library'...")
        record = {
            "titulo": data.get("titulo"),
            "autor": data.get("autor", "Neville Goddard"),
            "anio": data.get("año", "sin_ano"),
            "etiquetas": data.get("etiquetas", []),
            "frases_destacadas": data.get("frases_destacadas", []),
            "explicaciones_metafisicas": data.get("explicaciones_metafisicas", []),
            "testimonios": data.get("testimonios", []),
            "preguntas_verdadero_falso": data.get("preguntas_verdadero_falso", []),
            "audio_url": audio_url
        }
        
        supabase.table("library").insert(record).execute()
        print(f"-> ¡Insertado exitosamente!")

if __name__ == "__main__":
    # Nos movemos al directorio del script para que los paths relativos funcionen
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    seed_database()
    print("\n¡Sembrado de base de datos completado!")
