from typing import List
import open_clip
import torch
from langchain_core.embeddings import Embeddings
from app.core.config import settings
from PIL import Image

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
        with torch.no_grad():
            tokenized = self.tokenizer(texts).to(self.device)
            embeddings = self.model.encode_text(tokenized)
            embeddings /= embeddings.norm(dim=-1, keepdim=True)
            return embeddings.cpu().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
    
    def embed_image(self, image_path: str) -> List[float]:
        image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().tolist()[0]
