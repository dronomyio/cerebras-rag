#!/usr/bin/env python3
"""
Weaviate Ingestion Script for Ruppert's Book
--------------------------------------------
Ingests processed chunks from Ruppert's book into Weaviate.
"""

import os
import json
import weaviate
import logging
from dotenv import load_dotenv
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class WeaviateIngestor:
    def __init__(self):
        """Initialize the Weaviate ingestor with connection details."""
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        self.client = self._connect_to_weaviate()
        
    def _connect_to_weaviate(self):
        """Connect to Weaviate instance."""
        auth_config = weaviate.auth.AuthApiKey(api_key=self.weaviate_api_key)
        
        try:
            client = weaviate.Client(
                url=self.weaviate_url,
                auth_client_secret=auth_config if self.weaviate_api_key else None
            )
            logger.info(f"Connected to Weaviate at {self.weaviate_url}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    def create_schema(self):
        """Create the schema for Ruppert's book content."""
        # Define the class for book content
        ruppert_class = {
            "class": "RuppertContent",
            "description": "Content chunks from Ruppert's Statistics and Data Analysis for Financial Engineering book",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "content",
                    "description": "The text content of the chunk",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "chapterNumber",
                    "description": "Chapter number",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "chapterTitle",
                    "description": "Chapter title",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "sectionNumber",
                    "description": "Section number (if applicable)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "sectionTitle",
                    "description": "Section title (if applicable)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "hasCode",
                    "description": "Whether the chunk contains code examples",
                    "dataType": ["boolean"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "codeBlocks",
                    "description": "Code blocks contained in the chunk",
                    "dataType": ["string[]"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "codeLanguages",
                    "description": "Programming languages of the code blocks",
                    "dataType": ["string[]"],
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                }
            ]
        }
        
        # Create the schema
        try:
            if self.client.schema.exists("RuppertContent"):
                logger.info("RuppertContent class already exists, deleting it first")
                self.client.schema.delete_class("RuppertContent")
            
            self.client.schema.create_class(ruppert_class)
            logger.info("Created RuppertContent schema in Weaviate")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise
    
    def ingest_chunks(self, chunks_file):
        """Ingest chunks from the processed file into Weaviate."""
        try:
            with open(chunks_file, 'r') as f:
                chunks = json.load(f)
            
            logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
            
            # Batch import for better performance
            with self.client.batch as batch:
                batch.batch_size = 50
                
                for i, chunk in enumerate(tqdm(chunks, desc="Ingesting chunks")):
                    # Extract code blocks and languages
                    code_blocks = []
                    code_languages = []
                    for code_block in chunk.get("code_blocks", []):
                        code_blocks.append(code_block["code"])
                        code_languages.append(code_block["language"])
                    
                    # Prepare properties
                    properties = {
                        "content": chunk["content"],
                        "hasCode": chunk["metadata"].get("has_code", False),
                        "chapterNumber": chunk["metadata"].get("chapter_number", ""),
                        "chapterTitle": chunk["metadata"].get("chapter_title", ""),
                        "codeBlocks": code_blocks,
                        "codeLanguages": code_languages
                    }
                    
                    # Add section info if available
                    if "section_number" in chunk["metadata"]:
                        properties["sectionNumber"] = chunk["metadata"]["section_number"]
                    if "section_title" in chunk["metadata"]:
                        properties["sectionTitle"] = chunk["metadata"]["section_title"]
                    
                    # Add to batch
                    batch.add_data_object(
                        data_object=properties,
                        class_name="RuppertContent"
                    )
            
            logger.info(f"Successfully ingested {len(chunks)} chunks into Weaviate")
        except Exception as e:
            logger.error(f"Failed to ingest chunks: {e}")
            raise

def main():
    """Main function to run the ingestion process."""
    # Define paths
    chunks_file = "/data/output/chunks.json"
    
    # Check if chunks file exists
    if not os.path.exists(chunks_file):
        logger.error(f"Chunks file not found: {chunks_file}")
        # Try to extract the PDF first
        pdf_path = "/data/ruppert.pdf"
        output_dir = "/data/output"
        
        if os.path.exists(pdf_path):
            logger.info(f"Found PDF at {pdf_path}, extracting content...")
            from extract_pdf import PDFProcessor
            processor = PDFProcessor(pdf_path, output_dir)
            processor.process()
        else:
            logger.error(f"PDF file not found: {pdf_path}")
            return
    
    # Initialize and run the ingestor
    ingestor = WeaviateIngestor()
    ingestor.create_schema()
    ingestor.ingest_chunks(chunks_file)
    
    logger.info("Ingestion process completed successfully")

if __name__ == "__main__":
    main()
