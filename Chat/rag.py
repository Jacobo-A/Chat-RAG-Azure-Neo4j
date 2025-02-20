import os
from concurrent.futures import ThreadPoolExecutor
from processorDoc import ProcesadorDocumento, Chunk
from langchain_community.graphs.graph_document import Node, Relationship
from llm import get_embeddings, get_doc_transformer
from neo4jDb import get_graph_db

class DocumentoProcessor:
    def __init__(self, file_path, procesamiento_automatico=False, num_threads=20):
        self.file_path = file_path
        self.procesamiento_automatico = procesamiento_automatico
        self.num_threads = num_threads
        self.graph = get_graph_db()
        self.embedding_provider = get_embeddings()
        self.doc_transformer = get_doc_transformer()
        
    def procesar_documento(self):
        # Procesar documento
        self.procesador = ProcesadorDocumento(self.file_path, procesamiento_automatico=self.procesamiento_automatico)
        self.procesador.procesarDocumento()
        self.informacion = self.procesador.informacion
        self.chunks = Chunk(self.informacion)
        self.chunks_lista = self.chunks.chunks
        print(f"Total de chunks procesados: {len(self.chunks_lista)}")

    def process_chunk(self, chunk):
        filname = os.path.basename(chunk.metadata["source"])
        chunk_id = f"{filname}.{chunk.metadata['chunk_number']}"
        print(f"Processing - {chunk_id}")
        
        chunk_embedding = self.embedding_provider.embed_query(chunk.page_content)

        properties = {
            "filename": filname,
            "chunk_id": chunk_id,
            "text": chunk.page_content,
            "embedding": chunk_embedding
        }

        # Guardar en la base de datos
        self.graph.query("""
            MERGE (d:Document {id: $filename})
            MERGE (c:Chunk {id: $chunk_id}) ON CREATE SET c.text = $text
            MERGE (d)<-[:PART_OF]-(c)
            WITH c
            CALL db.create.setNodeVectorProperty(c, "textEmbedding", $embedding)
        """, properties)

        # Convertir los chunks a documentos de grafo
        graph_docs = self.doc_transformer.convert_to_graph_documents([chunk])

        for graph_doc in graph_docs:
            chunk_node = Node(id=chunk_id, type="Chunk")
            for node in graph_doc.nodes:
                graph_doc.relationships.append(
                    Relationship(
                        source=chunk_node,
                        target=node,
                        type="HAS_ENTITY"
                    )
                )

        self.graph.add_graph_documents(graph_docs)

    def procesar_chunks_con_hilos(self):
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            executor.map(self.process_chunk, self.chunks_lista)

    def crear_indice_vector(self):
        self.graph.query("""
            CREATE VECTOR INDEX `chunkVector`
            IF NOT EXISTS
            FOR (c: Chunk) ON (c.textEmbedding)
            OPTIONS {indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
            }};""")
    
    def ejecutar_procesamiento(self):
        self.procesar_documento()
        self.procesar_chunks_con_hilos()
        self.crear_indice_vector()