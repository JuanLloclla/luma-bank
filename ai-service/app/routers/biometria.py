from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.biometria_service import extraer_embedding, comparar_embeddings
from app.schemas.biometria_schema import (
    EmbeddingResponse,
    ComparacionRequest,
    ComparacionResponse,
)

router = APIRouter(prefix="/biometria", tags=["Biometría"])

@router.post("/embedding", response_model=EmbeddingResponse)
async def obtener_embedding(imagen: UploadFile = File(...)):
    if not imagen.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    imagen_bytes = await imagen.read()

    try:
        embedding = extraer_embedding(imagen_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la imagen: {str(e)}"
        )

    return EmbeddingResponse(embedding=embedding)

@router.post("/comparar", response_model=ComparacionResponse)
async def comparar_rostros(request: ComparacionRequest):
    if not request.embedding_dni or not request.embedding_selfie:
        raise HTTPException(
            status_code=400,
            detail="Los embeddings no pueden estar vacíos"
        )

    try:
        resultado = comparar_embeddings(
            request.embedding_dni,
            request.embedding_selfie
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al comparar rostros: {str(e)}"
        )

    return ComparacionResponse(**resultado)