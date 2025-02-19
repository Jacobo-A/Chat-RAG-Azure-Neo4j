from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv(".env", override=True)

# Función para conectarse a Neo4j con Langchain
def get_graph_db(database="neo4j"):
    """
    Devuelve una conexión a la base de datos especificada.
    """
    return Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        database=database # Se conecta a la BD especificada
    )

# Función para conectarse a Neo4j con el driver nativo
def get_driver():
    """
    Devuelve un driver de conexión al sistema de Neo4j.
    """
    return GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

def create_database(database_name):
    """
    Crea una nueva base de datos en Neo4j si no existe.
    """
    system_driver = get_driver()
    
    with system_driver.session(database="system") as session:
        cypher_query = f"CREATE DATABASE {database_name} IF NOT EXISTS"
        try:
            session.run(cypher_query)
            print(f"Base de datos '{database_name}' creada exitosamente.")
        except Exception as e:
            print(f"Error al crear la base de datos: {e}")
    
    system_driver.close()

    # Retorna la conexión a la nueva BD
    return get_graph_db(database_name)

def database_exists(database_name):
    """Verifica si una base de datos existe y la crea si no."""
    system_driver = get_driver()

    with system_driver.session(database="system") as session:
        cypher_query = f"SHOW DATABASES YIELD name WHERE name = '{database_name}'"
        result = session.run(cypher_query).single()

    system_driver.close()

    if result:
        print(f"La base de datos '{database_name}' ya existe.")
        return get_graph_db(database_name)  # Retorna la conexión a la BD existente
    else:
        print(f"La base de datos '{database_name}' no existe. Creándola...")
        return create_database(database_name)  # Crea la BD y retorna la conexión
    
