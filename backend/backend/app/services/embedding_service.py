import logging
import json
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = None
        return cls._instance

    def load_model(self):
        if not self.model:
            logger.info("Loading embedding model...")
            # Use 'all-MiniLM-L6-v2' - it's small (80MB) and fast
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded.")

    def generate_embedding(self, text: str) -> str:
        if not self.model:
            self.load_model()
        
        if not text:
            return None
            
        try:
            # Encode returns a numpy array
            vector = self.model.encode(text)
            # Convert to list and then JSON string for storage
            return json.dumps(vector.tolist())
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def cosine_similarity(self, vec1_json: str, vec2_json: str) -> float:
        try:
            v1 = np.array(json.loads(vec1_json))
            v2 = np.array(json.loads(vec2_json))
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        except Exception:
            return 0.0

embedding_service = EmbeddingService()
