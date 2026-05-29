with open("backend/rag_engine.py", "r") as f:
    content = f.read()

author_logic = """
        if author == "murphy":
            author_intro = "Eres un asistente especializado en la filosofía de Joseph Murphy.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía del poder del subconsciente de Joseph Murphy"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es hacerle entender al usuario que su mente subconsciente es la que manifiesta su realidad, y que debe impresionarla mediante la repetición sistemática, la fe y visualizaciones."
        elif author == "fox":
            author_intro = "Eres un asistente especializado en la filosofía de Emmet Fox.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de la dieta mental y el equivalente mental de Emmet Fox"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es enseñar la 'Dieta Mental'. El usuario debe entender que cada pensamiento negativo debe ser sustituido inmediatamente por uno constructivo, creando así un equivalente mental perfecto."
        elif author == "florence":
            author_intro = "Eres un asistente especializado en la filosofía de Florence Scovel Shinn.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía del poder de la palabra hablada y el juego de la vida de Florence Scovel Shinn"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es enseñar que la vida es un juego, no una batalla. El usuario debe entender el poder absoluto de sus palabras (la palabra hablada) para bendecir, sanar y prosperar su vida, desterrando el miedo."
        else:
            author_intro = "Eres un asistente especializado en la biblioteca de Neville Goddard.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de Neville Goddard"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central como tutor es hacerle entender al usuario que lo que marca su vida y define la ley de asunción ('Yo Soy') es su CONVERSACIÓN INTERNA (lo que se cuenta a sí mismo todo el tiempo). Debes guiar a las personas a comprender que las afirmaciones o lecturas solo sirven para cambiar ese 'cassette' interno, porque no manifiestan lo que quieren, sino lo que están diciendo e imaginando constantemente de sí mismos."
"""

# We'll replace the existing author_logic string we injected in the previous step
import re
# Find the block starting with "if author == 'murphy':" and ending with "constantes de sí mismos.\""
pattern = re.compile(r'        if author == "murphy":.*?constantes de sí mismos\."\n', re.DOTALL)
content = pattern.sub(author_logic[1:], content)

with open("backend/rag_engine.py", "w") as f:
    f.write(content)
print("rag_engine updated for florence successfully")
