"""
RAG Service for MediMitra - Medical Symptom Analysis
Uses PGVector for semantic search and BioMistral embeddings
"""

import psycopg2
import json
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class MedicalRAGService:
    """Medical RAG service using PGVector and domain-specific embeddings"""
    
    def __init__(self):
        """Initialize with medical domain embedding model"""
        try:
            # Use medical domain model (384 dimensions)
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_SEED)
            self.dimension = 384
            logger.info("Medical embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def get_specialists_for_symptoms(self, symptoms: str, threshold: float = 0.5) -> List[str]:
        """
        Get recommended specialists based on symptoms using RAG
        
        Args:
            symptoms: Patient's symptom description
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of specialist names
        """
        try:
            # Generate embedding for symptoms
            symptom_embedding = self.create_embedding(symptoms)
            if not symptom_embedding:
                logger.warning("Failed to generate embedding, returning default")
                return ['General Medicine']
            
            # Query PGVector for similar symptoms
            conn = self._get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT 
                    content, 
                    metadata, 
                    1 - (embedding <=> %s::vector) AS similarity
                FROM document_embeddings
                WHERE doc_type = 'symptom_mapping'
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """
            
            cur.execute(query, (symptom_embedding, symptom_embedding))
            results = cur.fetchall()
            
            cur.close()
            conn.close()
            
            # Extract specialists from results
            specialists = set()
            for content, metadata, similarity in results:
                logger.info(f"Match: {content[:50]}... (similarity: {similarity:.3f})")
                
                if similarity >= threshold:
                    # Parse metadata
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    # Add specialists from metadata
                    if 'specialists' in metadata:
                        specialists.update(metadata['specialists'])

            specialists.discard('General Medicine')
            specialist_list = list(specialists)
            specialist_list.insert(0, 'General Medicine')
            
            logger.info(f"Recommended specialists: {specialist_list}")
            return specialist_list[:5]  #Top 5

        except Exception as e:
            logger.error(f"Error in get_specialists_for_symptoms: {e}")
            return ['General Medicine']
    
    def get_medicine_instructions(self, medicine_text: str) -> Optional[str]:
        """
        Get medicine instructions from RAG (Future implementation)
        
        Args:
            medicine_text: Extracted medicine names from prescription
        
        Returns:
            Medicine instructions or None
        """
        try:
            # Generate embedding
            query_embedding = self.create_embedding(medicine_text)
            if not query_embedding:
                return None
            
            # Query PGVector for medicine information
            conn = self._get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT 
                    content, 
                    metadata,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM document_embeddings
                WHERE doc_type = 'medicine_info'
                ORDER BY embedding <=> %s::vector
                LIMIT 3
            """
            
            cur.execute(query, (query_embedding, query_embedding))
            results = cur.fetchall()
            
            cur.close()
            conn.close()
            
            if not results:
                return None
            
            # Compile instructions from top matches
            instructions = []
            for content, metadata, similarity in results:
                if similarity > 0.6:
                    instructions.append(content)
            
            return "\n\n".join(instructions) if instructions else None
            
        except Exception as e:
            logger.error(f"Error in get_medicine_instructions: {e}")
            return None
    
    def search_similar_cases(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        General similarity search (for future use cases)
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of similar documents with metadata
        """
        try:
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            query_sql = """
                SELECT 
                    content, 
                    metadata, 
                    doc_type,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM document_embeddings
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            
            cur.execute(query_sql, (query_embedding, query_embedding, top_k))
            results = cur.fetchall()
            
            cur.close()
            conn.close()
            
            # Format results
            return [
                {
                    'content': content,
                    'metadata': json.loads(metadata) if isinstance(metadata, str) else metadata,
                    'doc_type': doc_type,
                    'similarity': similarity
                }
                for content, metadata, doc_type, similarity in results
            ]
            
        except Exception as e:
            logger.error(f"Error in search_similar_cases: {e}")
            return []


# Singleton instance
_rag_service_instance = None

def get_rag_service() -> MedicalRAGService:
    """Get or create RAG service singleton"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = MedicalRAGService()
    return _rag_service_instance

# Export singleton instance
rag_service = get_rag_service()
