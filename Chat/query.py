from sentence_transformers import SentenceTransformer
import numpy as np
from neo4jDb import get_driver

class QueryProcessor:
    def __init__(self):
        # Cargar modelo de embeddings
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        self.driver = get_driver()

    def get_context(self, query_text):
        # Obtener el embedding de la consulta
        query_embedding = self.model.encode(query_text).tolist()  # Convertir a lista para Neo4j

        # Consulta en Neo4j con los embeddings generados
        cypher_query = """
        CALL db.index.vector.queryNodes('chunkVector', 1, $embedding)
        YIELD node, score
        RETURN node.text, score
        """
        
        # Ejecutar la consulta
        with self.driver.session(database="neo4j") as session:
            result = session.run(cypher_query, embedding=query_embedding)
            context = []
            for record in result:
                # Solo se agrega el texto al contexto
                context.append(record["node.text"])
                # Imprimir el puntaje
                print(f"Score: {record['score']}")
            return context

    def close(self):
        # Cerrar la conexión a la base de datos
        self.driver.close()
