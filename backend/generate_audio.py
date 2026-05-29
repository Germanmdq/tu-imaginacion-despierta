import os
import json
import asyncio
import edge_tts

# Directorios
JSON_DIR = "json_extraidos"
AUDIO_DIR = os.path.join(JSON_DIR, "audios")

# Voz de Jorge (México)
VOICE = "es-MX-JorgeNeural"

async def generate_audio_for_json(json_path, output_path):
    print(f"Generando audio para: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Armar el guion del audio
    texto_audio = ""
    
    if "texto_completo" in data and data["texto_completo"]:
        texto_audio += data["texto_completo"]
    else:
        texto_audio += f"Conferencia: {data.get('titulo', 'Sin Título')}.\n\n"
        if "explicaciones_metafisicas" in data:
            for exp in data["explicaciones_metafisicas"]:
                texto_audio += f"{exp}\n"
        if "testimonios" in data:
            for test in data["testimonios"]:
                if "historia_completa" in test:
                    texto_audio += f"{test['historia_completa']}\n\n"

    # Generar el audio usando edge-tts
    communicate = edge_tts.Communicate(texto_audio, VOICE)
    await communicate.save(output_path)
    print(f"Guardado: {output_path}")

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    for filename in os.listdir(JSON_DIR):
        if filename.endswith(".json"):
            json_path = os.path.join(JSON_DIR, filename)
            output_name = filename.replace(".json", ".mp3")
            output_path = os.path.join(AUDIO_DIR, output_name)
            
            if not os.path.exists(output_path):
                await generate_audio_for_json(json_path, output_path)
            else:
                print(f"El audio ya existe: {output_name}")

if __name__ == "__main__":
    asyncio.run(main())
