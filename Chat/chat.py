from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_neo4j import Neo4jChatMessageHistory
from llm import get_chat_llm
from neo4jDb import get_graph_db, get_driver
from query import QueryProcessor


class Chat:
    """
    Clase para manejar la conversación con historial en Neo4j.
    """

    def __init__(self, database):
        self.database = database
        self.graph_db = get_graph_db(database=self.database)
        self.chat_llm = get_chat_llm()
        self.query = QueryProcessor()

        # Prompt default para el chat
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Eres un chat para la plataforma de INTEGRA Sener México. Solo respondes en texto(no markdown)."),
                ("system", "{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )

        # Crear pipeline con historial
        self.chat_chain = self.prompt | self.chat_llm | StrOutputParser()
        self.chat_with_message_history = RunnableWithMessageHistory(
            self.chat_chain,
            self.get_memory,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

    def get_memory(self, session_id):
        """
        Retorna el historial de mensajes asociado a la sesión.
        """
        return Neo4jChatMessageHistory(session_id=session_id, graph=self.graph_db)
    

    def start_conversation(self, session_id=None):
        """
        Inicia el bucle de conversación con el usuario.
        """
        print("Chat iniciado. Escribe 'exit' para salir.")

        while (question  := input("> ")) != "exit":
            response = self.chat_with_message_history.invoke(
                {   
                    # se extrae el contexto.
                    "context": self.query.get_context(question), 
                    "question": question },
                config={
                    "configurable": {"session_id": session_id}
                },
            )
            print(response)

        # Cerrar la conexión a la base de datos
        self.query.close()


    def get_chat_history(self, session_id=None):
        """
        Extrae el historial de conversación desde Neo4j.
        """
        query = """
        MATCH (s:Session)-[:LAST_MESSAGE]->(last:Message)
        WHERE s.id = $session_id
        MATCH p = (last)<-[:NEXT*]-(msg:Message)
        UNWIND nodes(p) as msgs
        RETURN DISTINCT msgs.type, msgs.content
        """

        # Ejecutar la consulta
        driver = get_driver()
        with driver.session(database=self.database) as session:
            result = session.run(query, session_id=session_id)
            # Mostrar los resultados
            for record in result:
                print(f"Type: {record['msgs.type']}, Content: {record['msgs.content']}")
        driver.close()

        return None
    

