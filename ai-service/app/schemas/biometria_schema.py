from pydantic import BaseModel
from typing import List

class EmbeddingResponse(BaseModel):
    embedding: List[float]

class ComparacionRequest(BaseModel):
    embedding_dni: List[float]
    embedding_selfie: List[float]

class ComparacionResponse(BaseModel):
    match: bool
    score: float
    threshold: float