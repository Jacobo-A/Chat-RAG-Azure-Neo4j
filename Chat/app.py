import neo4jDb
from chat import Chat

# Idetnifaidor de la base de datos (incializar con un minuscula)
DB_ID = "u12345" 

# Se verifica si la base de datos ya existe
neo4jDb.database_exists(DB_ID)

# Se inicializa el chat
chat_test = Chat(DB_ID)
chat_test.start_conversation(session_id="ejemplo0123")

# Se obtiene el historial de la conversacion
chat_test.get_chat_history(session_id="ejemplo0123") 


# import llm

# llm.get_embeddings()
