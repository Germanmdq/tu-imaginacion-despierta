import re

with open("backend/rag_engine.py", "r") as f:
    content = f.read()

# 1. Update query signature
content = content.replace(
    'def query(self, user_query, api_key=None, top_k=5):',
    'def query(self, user_query, author="neville", api_key=None, top_k=5):'
)

# 2. Update search_similarity call
content = content.replace(
    'results = self.vector_store.search_similarity(user_query, top_k=top_k, api_key=key)',
    'results = self.vector_store.search_similarity(user_query, top_k=top_k, api_key=key, author=author)'
)

# 3. Add author variables before system prompt construction
author_logic = """
        if author == "murphy":
            author_intro = "Eres un asistente especializado en la filosofía de Joseph Murphy.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía del poder del subconsciente de Joseph Murphy"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es hacerle entender al usuario que su mente subconsciente es la que manifiesta su realidad, y que debe impresionarla mediante la repetición sistemática, la fe y visualizaciones."
        elif author == "fox":
            author_intro = "Eres un asistente especializado en la filosofía de Emmet Fox.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de la dieta mental y el equivalente mental de Emmet Fox"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central es enseñar la 'Dieta Mental'. El usuario debe entender que cada pensamiento negativo debe ser sustituido inmediatamente por uno constructivo, creando así un equivalente mental perfecto."
        else:
            author_intro = "Eres un asistente especializado en la biblioteca de Neville Goddard.\\n\\n"
            author_philosophy = "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de Neville Goddard"
            author_core = "3. ENSEÑANZA PRINCIPAL: Tu propósito central como tutor es hacerle entender al usuario que lo que marca su vida y define la ley de asunción ('Yo Soy') es su CONVERSACIÓN INTERNA (lo que se cuenta a sí mismo todo el tiempo). Debes guiar a las personas a comprender que las afirmaciones o lecturas solo sirven para cambiar ese 'cassette' interno, porque no manifiestan lo que quieren, sino lo que están diciendo e imaginando constantemente de sí mismos."
"""

content = content.replace('if asked_for_references:', author_logic + '\n        if asked_for_references:')

# 4. Replace hardcoded Neville text in the prompts with dynamic variables
# Intro
content = content.replace(
    '"Eres un asistente especializado en la biblioteca de Neville Goddard.\\n\\n"',
    'author_intro +'
)
content = content.replace(
    "'Hola, soy tu asistente para controlar la imaginación. Estoy aquí para ayudarte a explorar las enseñanzas de Neville Goddard y aplicarlas en tu vida.'",
    "'Hola, soy tu asistente para controlar la imaginación y explorar las enseñanzas de este autor.'"
)

# Philosophy
content = content.replace(
    "usar tu razonamiento para generarlos de manera creativa aplicando la filosofía de Neville Goddard. MUY IMPORTANTE:",
    "\" + author_philosophy + \". MUY IMPORTANTE:"
)

# Core teaching
content = content.replace(
    '"3. ENSEÑANZA PRINCIPAL: Tu propósito central como tutor es hacerle entender al usuario que lo que marca su vida y define la ley de asunción (\'Yo Soy\') es su CONVERSACIÓN INTERNA (lo que se cuenta a sí mismo todo el tiempo). Debes guiar a las personas a comprender que las afirmaciones o lecturas solo sirven para cambiar ese \'cassette\' interno, porque no manifiestan lo que quieren, sino lo que están diciendo e imaginando constantemente de sí mismos.\\n"',
    'author_core + "\\n"'
)

with open("backend/rag_engine.py", "w") as f:
    f.write(content)
print("rag_engine updated successfully")
