import numpy as np
import insightface
from insightface.app import FaceAnalysis
import cv2
import io
from PIL import Image
from app.core.config import settings

# Se inicializa una sola vez al arrancar el servicio
face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))

def extraer_embedding(imagen_bytes: bytes) -> list[float]:
    imagen = _bytes_a_bgr(imagen_bytes)
    faces = face_app.get(imagen)

    if not faces:
        raise ValueError("No se detectó ningún rostro en la imagen")

    # Si hay más de un rostro, tomar el más grande (mayor área del bounding box)
    if len(faces) > 1:
        faces = sorted(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            reverse=True
        )

    embedding = faces[0].embedding
    return embedding.tolist()

def comparar_embeddings(
    embedding_dni: list[float],
    embedding_selfie: list[float]
) -> dict:
    vec1 = np.array(embedding_dni)
    vec2 = np.array(embedding_selfie)

    # Cosine similarity
    score = float(
        np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    )

    return {
        "match": score >= settings.similarity_threshold,
        "score": round(score, 4),
        "threshold": settings.similarity_threshold,
    }

def _bytes_a_bgr(imagen_bytes: bytes) -> np.ndarray:
    imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(imagen), cv2.COLOR_RGB2BGR)