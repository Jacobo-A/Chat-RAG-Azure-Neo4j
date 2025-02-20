from paddleocr import PaddleOCR
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import fitz
import os

"""
Esta clase procesa un documento PDF para convertirlo en texto, 
identifica si es documento de imágenes o documento de texto, 
si es documento de imágenes se ejecuta un sistema de OCR, 
en su constructor recibe la ruta del documento y se puede especificar
 si el procesamiento del documento se hace al instanciar la clase
 o cuando el usuario lo decida con el método 'procesarDocumento'.
"""
class ProcesadorDocumento:

    """
    Carga el documento, checa si el documento es de tipo imagen o texto, 
    hace el procesamiento del archivo si el usuario lo indicó
    """
    def __init__(self, ruta, procesamiento_automatico = True):
        self.informacion = []
        self.__ruta = ruta
        self.__documento = PyPDFLoader(self.__ruta, extract_images = False)
        self.__documentoCargado = self.__documento.load()
        print(self.__documentoCargado[0].metadata)
        self.__plantillaMetadata = {'source':self.__documentoCargado[0].metadata.get('source'), 'total_pages':self.__documentoCargado[0].metadata.get('total_pages'), 'page':0, 'page_label':'1'}
        self.esImagen = self.__checarTipo()
        self.__ocr = PaddleOCR(use_angle_cls=True, lang='en') 

        if(procesamiento_automatico == True):
            self.procesarDocumento()

    """
    Comprueba si el documento cargado es de tipo imagen o tipo texto, 
    regresa un booleano verdadero si es imagen y falso si es texto.
    """
    def __checarTipo(self):
        for pagina in self.__documentoCargado:
            texto = pagina
            if texto and texto.page_content.strip():
                return False
            
        return True    

    """ 
    Procesa el documento de texto y guarda toda la información en la lista 'informacion'.
    """        
    def __procesarDocumentoTexto(self):
        self.informacion = self.__documentoCargado
        self.informacion.pop(0)

    """ 
    Extrae todas las imágenes del documento y las guarda en una lista 
    junto con el numero de pagina, devuelve esta lista al final.
    """
    def __extraerImagenesDocumento(self): 
        imagenes = []
        documento_pdf = fitz.open(self.__ruta)
        numeroPaginaImagen = []

        for numero_pagina in range(len(documento_pdf)):
            pagina = documento_pdf.load_page(numero_pagina)
            lista_imagenes = pagina.get_images(full=True)
            
            for index_imagen, img in enumerate(lista_imagenes):
                xref = img[0]
                base = documento_pdf.extract_image(xref)
                imagen_bytes = base["image"]
                imagenes.append(imagen_bytes)
                numeroPaginaImagen.append(numero_pagina)

        return zip(imagenes, numeroPaginaImagen)
    
    """ 
    Extrae el texto de una sola imagen usando un modelo de OCR 
    y devuelve el texto extraído en un solo string.
    """
    def __procesarImagen(self, imagen):
        resultado = self.__ocr.ocr(imagen, cls = True)
        textoAgrupado = ""

        for index in range(len(resultado)):
            res = resultado[index]
            for deteccionTexto in res:
                textoAgrupado += deteccionTexto[1][0] + " "
        
        return textoAgrupado
    
    """ 
    Extrae las imágenes del documento llamando la función 
    '__extraerImagenesDocumento' luego procesa cada una usando la función 
    '__procesarImagen', crea un objeto tipo 'Documento' y guarda toda la información ahí
    """
    def __procesarDocumentoImagenes(self): 
        self.informacion.clear()
        imagenes = self.__extraerImagenesDocumento()

        for imagen in imagenes:
            customMetadata = self.__plantillaMetadata
            customMetadata['page'] = imagen[1] #modificar metadata
            documentoImagen = Document(page_content = self.__procesarImagen(imagen[0]), metadata = customMetadata)
            self.informacion.append(documentoImagen)
    
    """ 
    Función a llamar cuando se quiera iniciar con el procesamiento del documento cargado.
    """
    def procesarDocumento(self):
        if(self.esImagen == True):
            self.__procesarDocumentoImagenes()
        else: 
            self.__procesarDocumentoTexto()
        return self.informacion


""" 
Esta clase separa en pequeños bloques o chunks de la lista de documentos recibida, 
tomando en cuenta los parámetros de tamaño del chunk y tamaño de superposición.
"""
class Chunk:
    """ 
    Constructor de la clase, toma como parámetro la lista de documentos a procesar, 
    además de que acepta otros parámetros opcionales con valores por defecto. 
    Se puede iniciar el procesamiento del texto en esta función si se indica.
    """
    def __init__(self, informacion, chunkingEnInicio = True, **kwargs):
        self.informacion = informacion
        self.tamanoChunk = kwargs.get('tamanoChunk', 1500)
        self.tamanoSuperPosicion = kwargs.get('tamanoSuperPosicion', 50)
        self.chunks = []
        if(chunkingEnInicio == True):
            self.crearChunks()
    
    """ 
    Procesar la lista de documentos y lo separa en una lista de chunks o bloques más pequeños.
    """
    def crearChunks(self, **kwargs):
        self.tamanoChunk = kwargs.get('tamanoChunk', self.tamanoChunk)
        self.tamanoSuperPosicion = kwargs.get('tamanoSuperPosicion', self.tamanoSuperPosicion)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = self.tamanoChunk, chunk_overlap = self.tamanoSuperPosicion)
        self.chunks = text_splitter.split_documents(self.informacion)

        # Añadir número de a los metadatos
        for index, chunk in enumerate (self.chunks):
            custom_metadata = chunk.metadata if hasattr(chunk, 'metadata') else {}
            custom_metadata['chunk_number'] = index+1
            chunk.metadata = custom_metadata