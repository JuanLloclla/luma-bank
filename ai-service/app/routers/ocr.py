from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import extraer_datos_dni
from app.schemas.ocr_schema import DniOcrResponse

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/dni", response_model=DniOcrResponse)
async def procesar_dni(imagen: UploadFile = File(...)):
    if not imagen.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    imagen_bytes = await imagen.read()
    
    try:
        datos = extraer_datos_dni(imagen_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error al procesar el DNI: {str(e)}"
        )

    return DniOcrResponse(**datos)