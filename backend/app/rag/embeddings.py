import hashlib
from typing import List
import open_clip
import torch
from langchain_core.embeddings import Embeddings
from app.core.config import settings
from PIL import Image
from cachetools import LRUCache

# LRU cache for text embedding vectors (deterministic for same input)
_text_embedding_cache = LRUCache(maxsize=512)

class OpenCLIPEmbeddings(Embeddings):
    def __init__(self):
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            settings.OPENCLIP_MODEL_NAME, 
            pretrained=settings.OPENCLIP_PRETRAINED
        )
        self.tokenizer = open_clip.get_tokenizer(settings.OPENCLIP_MODEL_NAME)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, using cache for previously seen strings."""
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in _text_embedding_cache:
                results[i] = _text_embedding_cache[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch-embed only uncached texts
        if uncached_texts:
            with torch.no_grad():
                tokenized = self.tokenizer(uncached_texts).to(self.device)
                embeddings = self.model.encode_text(tokenized)
                embeddings /= embeddings.norm(dim=-1, keepdim=True)
                new_vectors = embeddings.cpu().tolist()

            for j, idx in enumerate(uncached_indices):
                cache_key = hashlib.md5(uncached_texts[j].encode()).hexdigest()
                _text_embedding_cache[cache_key] = new_vectors[j]
                results[idx] = new_vectors[j]

        return results

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
    
    def embed_image(self, image_path: str) -> List[float]:
        image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().tolist()[0]

_embedding_model_instance = None

def get_embeddings_model() -> OpenCLIPEmbeddings:
    """Lazy-loaded singleton instance for the embedding model."""
    global _embedding_model_instance
    if _embedding_model_instance is None:
        print("Initializing OpenCLIPEmbeddings model (Singleton)...")
        _embedding_model_instance = OpenCLIPEmbeddings()
    return _embedding_model_instance
