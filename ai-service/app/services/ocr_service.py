import numpy as np
import easyocr
from PIL import Image
import io
import re

reader = easyocr.Reader(["es", "en"], gpu=False)

ETIQUETAS_DNI = {
    "FECHA", "INSCRIPCION", "EMISION", "CADUCIDAD",
    "NACIMIENTO", "SEXO", "ESTADO", "CIVIL", "UBIGEO",
    "PRIMER", "SEGUNDO", "APELLIDO", "NOMBRES", "PRE",
    "DOCUMENTO", "NACIONAL", "IDENTIDAD", "REPUBLICA",
    "PERU", "REGISTRO", "DNI", "CUI", "CONSTANCIA",
    "SUFRAGIO", "DEPARTAMENTO", "PROVINCIA", "DISTRITO"
}

def es_etiqueta(texto: str) -> bool:
    palabras = texto.upper().split()
    return any(p in ETIQUETAS_DNI for p in palabras)

def es_dato_nombre(texto: str) -> bool:
    texto_up = texto.upper().strip()
    if not re.match(r"^[A-ZÁÉÍÓÚÑ]+$", texto_up):
        return False
    if es_etiqueta(texto_up):
        return False
    if len(texto_up) < 2:
        return False
    return True

def normalizar_nombre(texto: str) -> str:
    separado = re.sub(r"([a-z])([A-Z])", r"\1 \2", texto)
    resultado = separado.upper().strip()
    resultado = re.sub(r"\s+", " ", resultado)
    # Si la última palabra es una sola letra, pegarla a la anterior
    partes = resultado.split()
    if len(partes) > 1 and len(partes[-1]) == 1:
        partes[-2] = partes[-2] + partes[-1]
        partes = partes[:-1]
    return " ".join(partes)

def normalizar_fecha(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r"^(\d{2})(\d{2})\s(\d{4})$", r"\1 \2 \3", texto)
    return re.sub(r"\s", "/", texto)

def contiene_apellido(texto: str) -> bool:
    # Cubre: APELLIDO, APELLIDLO, APOLLIDO, APULLIDO, etc.
    return bool(re.search(r"AP[AEOU][LP]", texto.upper()))

def extraer_datos_dni(imagen_bytes: bytes) -> dict:
    imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
    imagen_np = np.array(imagen)

    resultado = reader.readtext(imagen_np)

    #print("=== RAW OCR OUTPUT ===")
    #for bbox, texto, confianza in resultado:
    #    print(f"  [{confianza:.2f}] {texto}")
    #print("=== FIN RAW OUTPUT ===")

    textos = [(texto, confianza) for _, texto, confianza in resultado]
    return _parsear_dni(textos)

def _parsear_dni(textos: list[tuple]) -> dict:
    datos = {
        "numero_dni": "",
        "nombres": "",
        "apellidos": "",
        "fecha_nacimiento": "",
        "fecha_vencimiento": "",
        "departamento": "",
    }

    # ── 1. DNI ────────────────────────────────────────────────────────────
    for texto, _ in textos:
        match = re.search(r"DNI\s*(\d{8})", texto.upper())
        if match:
            datos["numero_dni"] = match.group(1)
            break
        if re.fullmatch(r"\d{8}", texto):
            datos["numero_dni"] = texto
            break

    # ── 2. Apellidos desde etiquetas ──────────────────────────────────────
    primer_apellido = ""
    segundo_apellido = ""

    for i, (texto, _) in enumerate(textos):
        texto_up = texto.upper()

        if "PRIMER" in texto_up and contiene_apellido(texto_up):
            for j in range(i + 1, min(i + 6, len(textos))):
                candidato, _ = textos[j]
                if es_dato_nombre(candidato):
                    primer_apellido = normalizar_nombre(candidato)
                    break

        if "SEGUNDO" in texto_up and contiene_apellido(texto_up):
            for j in range(i + 1, min(i + 6, len(textos))):
                candidato, _ = textos[j]
                if es_dato_nombre(candidato):
                    segundo_apellido = normalizar_nombre(candidato)
                    break

    if primer_apellido or segundo_apellido:
        datos["apellidos"] = f"{primer_apellido} {segundo_apellido}".strip()

    # ── 3. Nombres desde etiqueta "Pre Nombres" ───────────────────────────
    for i, (texto, _) in enumerate(textos):
        if "PRE" in texto.upper() and "NOMB" in texto.upper():
            for j in range(i + 1, min(i + 5, len(textos))):
                candidato, _ = textos[j]
                if es_dato_nombre(candidato):
                    datos["nombres"] = normalizar_nombre(candidato)
                    break

    # ── 4. Fallback MRZ ───────────────────────────────────────────────────
    if not datos["apellidos"] or not datos["nombres"]:
        for texto, _ in textos:
            texto_limpio = texto.replace(" ", "").upper()
            if re.match(r"^[A-Z<]{10,}$", texto_limpio) and "<<" in texto_limpio:
                partes = texto_limpio.split("<<")
                if len(partes) >= 2:
                    if not datos["apellidos"]:
                        datos["apellidos"] = partes[0].replace("<", " ").strip()
                    if not datos["nombres"]:
                        datos["nombres"] = partes[1].replace("<", " ").strip()
                break

    # ── 5. Fechas por etiqueta ────────────────────────────────────────────
    patron_fecha = re.compile(r"\d{2}[\s/]?\d{2}[\s/]\d{4}")

    for i, (texto, _) in enumerate(textos):
        texto_up = texto.upper()

        if "NACIM" in texto_up:
            for j in range(i + 1, min(i + 6, len(textos))):
                candidato, _ = textos[j]
                if patron_fecha.search(candidato):
                    datos["fecha_nacimiento"] = normalizar_fecha(candidato)
                    break

        if "CADUCID" in texto_up:
            for j in range(i + 1, min(i + 5, len(textos))):
                candidato, _ = textos[j]
                if patron_fecha.search(candidato):
                    datos["fecha_vencimiento"] = normalizar_fecha(candidato)
                    break

    return datos
