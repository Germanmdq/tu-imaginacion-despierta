import os
import json
import time
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Usamos Groq Llama 3.1 para procesamiento rápido de texto largo
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DOCS_DIR = "../documents/neville"
OUT_DIR = "../json_extraidos"

def split_pdf_by_pages(pdf_path, chunk_size=10):
    """Extrae el texto del PDF y lo agrupa de a N páginas."""
    reader = PdfReader(pdf_path)
    chunks = []
    current_chunk = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            current_chunk += text + "\n"
        
        # Cada 'chunk_size' páginas, guardamos el bloque
        if (i + 1) % chunk_size == 0:
            chunks.append(current_chunk)
            current_chunk = ""
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def process_chunk_with_gemini(text_chunk, is_first_chunk):
    """Envía el fragmento a Gemini para que lo estructure."""
    
    prompt = """
Eres un editor experto y teólogo de Neville Goddard. A continuación te pasaré un bloque de texto en crudo escaneado de un PDF. 
Tu trabajo es corregir errores tipográficos y ortográficos generados por el OCR, y estructurar el contenido en JSON.

IMPORTANTE: El texto puede contener una o varias "conferencias" o "capítulos". Debes devolver un ARRAY de objetos JSON, donde cada objeto represente una conferencia o tema distinto encontrado en este bloque.

Para cada conferencia encontrada, el JSON debe tener ESTRICTAMENTE esta estructura:
{
  "titulo": "Título de la conferencia",
  "autor": "neville",
  "año": "Año (si se menciona, sino 'sin_ano')",
  "texto_completo": "AQUÍ DEBES PONER EL TEXTO COMPLETO Y CORREGIDO PALABRA POR PALABRA. NO RESUMAS. CORRIGE ERRORES OCR.",
  "etiquetas": ["etiqueta1", "etiqueta2"],
  "frases_destacadas": ["Frase muy corta 1", "Frase muy corta 2"],
  "explicaciones_metafisicas": ["Resumen conceptual 1", "Resumen conceptual 2"],
  "testimonios": [{"categoria": "Salud/Dinero", "historia_completa": "Historia contada por Neville detallada sin resumir"}],
  "preguntas_verdadero_falso": [{"pregunta": "...", "opciones": ["Verdadero", "Falso"], "respuesta_correcta": "Verdadero"}]
}

Devuelve SOLO el JSON válido, sin bloques de código markdown, solo el raw JSON.
Texto a procesar:
""" + text_chunk

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Solo debes devolver JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        # Parse the JSON response
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
            print(f"Texto recibido: {response.choices[0].message.content[:200]}...")
            return None
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            print(f"Límite de cuota alcanzado (429). Esperando 60 segundos antes de reintentar...")
            time.sleep(60)
            # Reintento recursivo
            return process_chunk_with_gemini(text_chunk, is_first_chunk)
        else:
            print(f"Error procesando chunk con Gemini: {e}")
            return None

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Procesamos TODOS los PDFs
    pdf_files = [f for f in os.listdir(DOCS_DIR) if f.endswith('.pdf')]
    pdf_files.sort()
    
    for pdf_file in pdf_files:
        test_pdf = os.path.join(DOCS_DIR, pdf_file)
        # Extraer el número del tomo (ej: "01" de "01-Tomo-I...")
        tomo_prefix = pdf_file.split('-')[0] if '-' in pdf_file else "tomoX"
        
        print(f"\n==============================================")
        print(f"Extrayendo texto de {test_pdf}...")
        chunks = split_pdf_by_pages(test_pdf, chunk_size=10)
        print(f"PDF dividido en {len(chunks)} bloques de 10 páginas.")
        
        all_conferences = []
        
        for idx, chunk in enumerate(chunks):
            print(f"Enviando bloque {idx+1}/{len(chunks)} a Gemini...")
            results = process_chunk_with_gemini(chunk, idx == 0)
            
            if results and isinstance(results, list):
                # Guardar CADA conferencia al instante para no perder datos si crashea
                for i, conf in enumerate(results):
                    # Usar un ID único basado en el bloque y el índice de conferencia
                    conf_id = f"{idx}_{i}"
                    safe_title = conf.get("titulo", f"conferencia_{conf_id}").replace(" ", "_").replace("/", "").lower()
                    output_file = os.path.join(OUT_DIR, f"{tomo_prefix}_{conf_id}_{safe_title}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(conf, f, ensure_ascii=False, indent=2)
                    print(f" -> Guardado: {output_file}")
            
            time.sleep(2) # Respetar límites de API

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
