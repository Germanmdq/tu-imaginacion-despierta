import os
import re
import datetime
import google.generativeai as genai
from groq import Groq
from backend.vector_store import VectorStoreManager
from backend.scheduler import schedule_task, send_telegram_to_user, load_telegram_users

def clean_source_name(filename):
    mapping = {
        "01-Tomo-I-El-Poder-de-la-Imaginacion.pdf": "El Poder de la Imaginación",
        "02-Tomo-II-Vivir-Desde-el-Deseo-Cumplido.pdf": "Vivir Desde el Deseo Cumplido",
        "03-Tomo-III-La-Promesa-y-el-Despertar-Interior.pdf": "La Promesa y el Despertar Interior",
        "04-Tomo-IV-Escritura-Simbolo-y-Revelacion.pdf": "Escritura, Símbolo y Revelación",
        "05-Tomo-V-El-Hombre-Dios-y-la-Imaginacion.pdf": "El Hombre, Dios y la Imaginación",
        "06-Tomo-VI-Fe-Vision-y-Experiencia.pdf": "Fe, Visión y Experiencia",
        "07-Tomo-VII-Ultimas-Conferencias-y-Ensenanzas-Finales.pdf": "Últimas Conferencias y Enseñanzas Finales",
        "08-Tomo-VIII-Libros-Lecciones-y-Conferencias-de-Radio.pdf": "Libros, Lecciones y Conferencias de Radio",
        "introduccion_neville.txt": "Introducción a Neville Goddard"
    }
    if filename in mapping:
        return mapping[filename]
        
    # Fallback to cleaning the filename automatically
    name, _ = os.path.splitext(filename)
    cleaned = name.replace("-", " ").replace("_", " ")
    cleaned = re.sub(r'^\d+\s+Tomo\s+[IVXLCDM]+\s+', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip().title()

# Tomes that are primarily lecture collections — page numbers are meaningless there
LECTURE_TOMES = {
    "07-Tomo-VII-Ultimas-Conferencias-y-Ensenanzas-Finales.pdf",
    "08-Tomo-VIII-Libros-Lecciones-y-Conferencias-de-Radio.pdf",
}

# Regex to detect a lecture title line like: "01. El descubrimiento de Jeremías"
_LECTURE_TITLE_RE = re.compile(
    r'^\s*\d{1,3}[.)\-]\s+([A-ZÁÉÍÓÚÜÑ][\w\s,.–\-áéíóúüñÁÉÍÓÚÜÑ()]{3,80})',
    re.MULTILINE
)

def extract_conference_title(text):
    """Try to find a numbered lecture title in the chunk text."""
    match = _LECTURE_TITLE_RE.search(text)
    if match:
        return match.group(1).strip()
    return ""

def build_location_label(source_filename, page, chapter, chunk_text=""):
    """Return a human-readable location string, or empty string if not meaningful."""
    # For lecture tomes: try to extract the real conference title from the text
    if source_filename in LECTURE_TOMES:
        title = extract_conference_title(chunk_text)
        return title  # could be empty string — that's fine, no page shown
    # For other tomes: use chapter if it's a real title (not "Página X")
    if chapter and chapter.strip() and not chapter.strip().lower().startswith("página"):
        return chapter.strip()
    return ""

class RAGEngine:
    def __init__(self, db_path="db", collection_name="neville_goddard"):
        self.vector_store = VectorStoreManager(db_path, collection_name)
        
    def query(self, user_query, author="neville", api_key=None, top_k=5):
        """
        Retrieves matching chunks and calls Gemini model to generate a response.
        """
        key = api_key or os.environ.get("GEMINI_API_KEY")
        
        # 1. Search for similar document chunks
        results = self.vector_store.search_similarity(user_query, top_k=top_k, api_key=key, author=author)
        
        # Determine current system time for reference
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not results:
            # No files indexed or no matching content
            groq_client = Groq(api_key=groq_api_key)
            response = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Responde a la siguiente pregunta basándote en tu conocimiento general, ya que no se encontraron documentos locales."
                    },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3
            )
            return {
                "answer": response.choices[0].message.content,
                "sources": [],
                "warning": "No se encontraron documentos en la base de datos vectorial."
            }
            
        # 2. Build the context string
        context_blocks = []
        for i, res in enumerate(results):
            meta = res["metadata"]
            source = meta.get("source", "Desconocido")
            page = meta.get("page", "?")
            chapter = meta.get("chapter", "")
            location = f"Libro: {clean_source_name(source)}"
            if chapter:
                location += f" ({chapter})"
            elif page:
                location += f" (Pág. {page})"
                
            context_blocks.append(f"--- FRAGMENTO {i+1} ---\nOrigen: {location}\nContenido:\n{res['text']}\n")
            
        context_str = "\n".join(context_blocks)
        
        # 3. Check if user explicitly asked for references/sources
        reference_keywords = ["fuente", "cita", "libro", "conferencia", "página", "pag", "dónde dice", "dónde habla", "referencia", "documento", "tomo", "origen"]
        asked_for_references = any(kw in user_query.lower() for kw in reference_keywords)
        
        # 4. Construct System Prompt
        # Build list of registered Telegram users for context
        registered_users = load_telegram_users()
        users_list = ", ".join(
            f"{u['first_name']} (@{u['username']})" if u.get('username') else u['first_name']
            for u in registered_users.values()
        ) if registered_users else "ninguno registrado aún"

        scheduling_rules = (
            f"La fecha y hora actual del sistema es: {current_time_str}. Usa este dato de referencia para calcular fechas y horas relativas si el usuario te pide programar un recordatorio.\n"
            "Reglas de Mensajería y Programación:\n"
            "8. PROGRAMAR RECORDATORIO: Si el usuario pide programar un mensaje para una fecha/hora específica, al final de tu respuesta agrega: "
            "[PROGRAMAR: plataforma=\"telegram\", fecha_hora=\"YYYY-MM-DD HH:MM:SS\", texto=\"mensaje\"]\n"
            "9. ENVIAR AHORA A UN USUARIO: Si el usuario dice que quiere que le envíes mensajes a otra persona por Telegram (por nombre o @usuario), "
            f"los usuarios registrados en el bot son: {users_list}. "
            "Si el usuario pedido está registrado, al final de tu respuesta agrega: [ENVIAR_TELEGRAM: usuario=\"nombre_o_@username\", texto=\"mensaje\"]. "
            "Si el usuario NO está registrado, explícale que esa persona primero tiene que escribirle a @NevilleDespierta_bot en Telegram (con /start) para registrarse.\n"
            "10. REGISTRO: Si alguien quiere recibir mensajes por Telegram, indícale simplemente: 'Tocá el botón azul \"Conectar Telegram\" que ves arriba en la pantalla. Con un toque se abre el bot y solo tenés que presionar START.' No des más instrucciones que esas.\n\n"
        )
        
        
        if author == "murphy":
            author_intro = "Eres un asistente especializado en la filosofía de Joseph Murphy.\n\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía del poder del subconsciente de Joseph Murphy"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es hacerle entender al usuario que su mente subconsciente es la que manifiesta su realidad, y que debe impresionarla mediante la repetición sistemática, la fe y visualizaciones."
        elif author == "fox":
            author_intro = "Eres un asistente especializado en la filosofía de Emmet Fox.\n\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de la dieta mental y el equivalente mental de Emmet Fox"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es enseñar la 'Dieta Mental'. El usuario debe entender que cada pensamiento negativo debe ser sustituido inmediatamente por uno constructivo, creando así un equivalente mental perfecto."
        else:
            author_intro = "Eres un asistente especializado en la biblioteca de Neville Goddard.\n\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de Neville Goddard"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central como tutor es hacerle entender al usuario que Dios ES literalmente su propia y maravillosa imaginación humana. No es una 'herramienta divina' ni una energía externa. Dios es el Hombre. Y lo que marca su vida y define la ley de asunción ('Yo Soy') es su CONVERSACIÓN INTERNA (lo que se cuenta a sí mismo todo el tiempo). Debes guiar a las personas a comprender que las afirmaciones o lecturas solo sirven para cambiar ese 'cassette' interno, porque no manifiestan lo que quieren, sino lo que están diciendo e imaginando constantemente de sí mismos."

        if asked_for_references:
            system_prompt = (
                author_intro +
                "Tu tarea principal es responder las preguntas del usuario basándote de forma estricta y ÚNICAMENTE en los fragmentos de documentos provistos en el CONTEXTO. Sin embargo, si el usuario te hace una pregunta general sobre esta web (ej. qué es esta web, cómo funciona esta página, quién eres, cuál es tu propósito o de qué trata este buscador), debes responder con exactamente este mensaje: 'Hola, soy tu asistente para controlar la imaginación y explorar las enseñanzas de este autor.'\n\n"
                f"{scheduling_rules}"
                "Reglas importantes:\n"
                "1. Responde de manera clara, detallada, fluida y en español, capturando el tono inspirador del autor.\n"
                "2. Usa la información del contexto como base estricta para la filosofía y los conceptos. Sin embargo, si el usuario te pide crear afirmaciones, ejercicios, consejos, planes o ejemplos prácticos, DEBES " + author_philosophy + ". MUY IMPORTANTE:\n"
                " - Si creas afirmaciones, estas DEBEN ser frases muy cortas (de 1 a 5 palabras máximo), naturales y conversacionales que den por sentado que su deseo ya es un hecho consumado en su vida diaria. Ejemplos de lo que DEBES responder: 'Qué bien nos llevamos', 'Cómo me ama', 'Mi negocio es un éxito', 'Tengo dinero de sobra', 'Soy muy abundante'. Jamás uses la palabra 'atraer', 'deseo', 'voy a', 'pronto' ni hables del futuro. Tú SIEMPRE debes responder entregando la lista de afirmaciones que te piden usando el tiempo presente (estado del Yo Soy). ADEMÁS, después de entregar las afirmaciones, agrega una nota breve diciendo: 'Recuerda adaptar estas frases a tu vocabulario cotidiano, ya que deben sonar 100% naturales para ti. Si quieres dime de qué zona eres y te ayudo a traducirlas a tu forma de hablar.' Nunca te niegues a dar afirmaciones.\n"
                " - Si el usuario te pide un PLAN (plan de manifestación, rutina, etc.), DEBES estructurarle específicamente: 1) Cuál debe ser su conversación interna durante el día, 2) Qué tiene que hacer exactamente antes de acostarse (el estado afín al sueño / SATS), y 3) Cómo debe operar al despertarse y a lo largo del día. Todo desde la asunción estricta de que su deseo ya es un hecho.\n" +
                author_core + "\n" +
                "4. En tu respuesta, DEBES insertar citas o referencias a los fragmentos de origen utilizando el formato numérico [1], [2], etc. Por ejemplo: 'Como se menciona en el texto [1], la imaginación crea la realidad...'\n"
                "5. Si la respuesta no puede encontrarse en el contexto ni puede deducirse o crearse aplicando la filosofía de Neville (y no es una pregunta general sobre el funcionamiento de la web), di explícitamente: 'Sinceramente, no recuerdo esa historia o detalle en este momento. Quizás lo mencioné con otras palabras o esté recordando otra conferencia, pero ahora mismo se me escapa. ¿Hay algún otro tema del que quieras que hablemos?'\n"
                "5. NO utilices saludos ni te dirijas al usuario con apodos o fórmulas solemnes como 'Amado buscador', 'Querido estudiante', 'Amigo', etc. Responde directamente a la pregunta sin preámbulos ceremoniales.\n"
                "6. NO estructures tu respuesta con listas, viñetas, guiones ni enumeraciones (nada de ítems). Escribe la respuesta de forma totalmente narrativa, usando párrafos continuos y fluidos, integrando las citas [1], [2] dentro de la redacción de manera natural.\n"
                "7. IMPORTANTE: LA RESPUESTA DEBE SER REDACTADA EXCLUSIVAMENTE EN PÁRRAFOS CONTINUOS Y FLUIDOS. ESTÁ COMPLETAMENTE PROHIBIDO EL USO DE LISTAS, VIÑETAS, ITEMS O ENUMERACIONES (como *, -, 1., etc.). NUNCA utilices emojis o emoticonos en tu respuesta (ej. ni cerebros, ni caritas, ni destellos). Escribe solo texto plano y serio.\n\n"
                f"CONTEXTO:\n{context_str}"
            )
        else:
            system_prompt = (
                author_intro +
                "Tu tarea principal es responder las preguntas del usuario basándote de forma estricta y ÚNICAMENTE en los fragmentos de documentos provistos en el CONTEXTO. Sin embargo, si el usuario te hace una pregunta general sobre esta web (ej. qué es esta web, cómo funciona esta página, quién eres, cuál es tu propósito o de qué trata este buscador), debes responder con exactamente este mensaje: 'Hola, soy tu asistente para controlar la imaginación y explorar las enseñanzas de este autor.'\n\n"
                f"{scheduling_rules}"
                "Reglas importantes:\n"
                "1. Responde de manera clara, detallada, fluida y en español, capturando el tono inspirador del autor.\n"
                "2. Usa la información del contexto como base estricta para la filosofía y los conceptos. Sin embargo, si el usuario te pide crear afirmaciones, ejercicios, consejos, planes o ejemplos prácticos, DEBES " + author_philosophy + ". MUY IMPORTANTE:\n"
                " - Si creas afirmaciones, estas DEBEN ser frases muy cortas (de 1 a 5 palabras máximo), naturales y conversacionales que den por sentado que su deseo ya es un hecho consumado en su vida diaria. Ejemplos de lo que DEBES responder: 'Qué bien nos llevamos', 'Cómo me ama', 'Mi negocio es un éxito', 'Tengo dinero de sobra', 'Soy muy abundante'. Jamás uses la palabra 'atraer', 'deseo', 'voy a', 'pronto' ni hables del futuro. Tú SIEMPRE debes responder entregando la lista de afirmaciones que te piden usando el tiempo presente (estado del Yo Soy). ADEMÁS, después de entregar las afirmaciones, agrega una nota breve diciendo: 'Recuerda adaptar estas frases a tu vocabulario cotidiano, ya que deben sonar 100% naturales para ti. Si quieres dime de qué zona eres y te ayudo a traducirlas a tu forma de hablar.' Nunca te niegues a dar afirmaciones.\n"
                " - Si el usuario te pide un PLAN (plan de manifestación, rutina, etc.), DEBES estructurarle específicamente: 1) Cuál debe ser su conversación interna durante el día, 2) Qué tiene que hacer exactamente antes de acostarse (el estado afín al sueño / SATS), y 3) Cómo debe operar al despertarse y a lo largo del día. Todo desde la asunción estricta de que su deseo ya es un hecho.\n" +
                author_core + "\n" +
                "4. IMPORTANTE: NO DEBES insertar ninguna cita numérica (ej. no uses [1] o [2]) ni hacer ninguna referencia escrita al origen de los textos o fragmentos en tu respuesta. Responde directamente a la idea planteada como si fuera tu propio discurso fluido. ESTÁ ESTRICTAMENTE PROHIBIDO usar las palabras 'fragmento', 'documento', 'texto' o decir 'esto se encuentra en...'. Habla como si el conocimiento fuera tuyo.\n"
                "5. Si la respuesta no puede encontrarse en el contexto ni puede deducirse o crearse aplicando la filosofía de Neville (y no es una pregunta general sobre el funcionamiento de la web), di explícitamente: 'Sinceramente, no recuerdo esa historia o detalle en este momento. Quizás lo mencioné con otras palabras o esté recordando otra conferencia, pero ahora mismo se me escapa. ¿Hay algún otro tema del que quieras que hablemos?'\n"
                "5. NO utilices saludos ni te dirijas al usuario con apodos o fórmulas solemnes como 'Amado buscador', 'Querido estudiante', 'Amigo', etc. Responde directamente a la pregunta sin preámbulos ceremoniales.\n"
                "6. NO estructures tu respuesta con listas, viñetas, guiones ni enumeraciones (nada de ítems). Escribe la respuesta de forma totalmente narrativa, usando párrafos continuos y fluidos de manera natural.\n"
                "7. IMPORTANTE: LA RESPUESTA DEBE SER REDACTADA EXCLUSIVAMENTE EN PÁRRAFOS CONTINUOS Y FLUIDOS. ESTÁ COMPLETAMENTE PROHIBIDO EL USO DE LISTAS, VIÑETAS, ITEMS O ENUMERACIONES (como *, -, 1., etc.). NUNCA utilices emojis o emoticonos en tu respuesta (ej. ni cerebros, ni caritas, ni destellos). Escribe solo texto plano y serio.\n\n"
                f"CONTEXTO:\n{context_str}"
            )
            
        # 5. Generate answer with Groq (Llama 3.1 8B)
        try:
            groq_client = Groq(api_key=groq_api_key)
            response = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3
            )
            
            # Parse scheduler instructions from the response text
            answer_text = response.choices[0].message.content

            # Tag 1: Schedule a future message [PROGRAMAR: ...]
            pattern = r'\[PROGRAMAR:\s+plataforma="([^"]+)",\s+fecha_hora="([^"]+)",\s+texto="([^"]+)"\]'
            match = re.search(pattern, answer_text)
            if match:
                platform = match.group(1)
                scheduled_time = match.group(2)
                message_text = match.group(3)
                try:
                    schedule_task(message_text, scheduled_time, platform)
                    answer_text = answer_text.replace(match.group(0), "").strip()
                except Exception as err:
                    print(f"Error programando recordatorio desde RAG: {err}")

            # Tag 2: Send immediately to a specific Telegram user [ENVIAR_TELEGRAM: usuario="x", texto="y"]
            pattern2 = r'\[ENVIAR_TELEGRAM:\s+usuario="([^"]+)",\s+texto="([^"]+)"\]'
            match2 = re.search(pattern2, answer_text)
            if match2:
                target_user = match2.group(1)
                msg_text = match2.group(2)
                try:
                    sent = send_telegram_to_user(target_user, msg_text)
                    answer_text = answer_text.replace(match2.group(0), "").strip()
                    if not sent:
                        answer_text += f"\n\n(No pude encontrar a '{target_user}' en los usuarios registrados del bot.)"
                except Exception as err:
                    print(f"Error enviando Telegram desde RAG: {err}")
            
            # 6. Format sources for the UI (only if user explicitly asked for them)
            sources = []
            
            if asked_for_references:
                for i, res in enumerate(results):
                    meta = res["metadata"]
                    raw_source = meta.get("source", "Desconocido")
                    page = meta.get("page", 0)
                    chapter = meta.get("chapter", "")
                    location_label = build_location_label(raw_source, page, chapter, chunk_text=res["text"])
                    sources.append({
                        "id": i + 1,
                        "source": clean_source_name(raw_source),
                        "page": page,
                        "chapter": chapter,
                        "location_label": location_label,
                        "text": res["text"][:300] + "..." if len(res["text"]) > 300 else res["text"],
                        "full_text": res["text"],
                        "score": res["score"]
                    })
                
            return {
                "answer": answer_text,
                "sources": sources
            }
        except Exception as e:
            print(f"Error generando respuesta RAG: {e}")
            raise e
