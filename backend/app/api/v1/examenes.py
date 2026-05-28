from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def create_examen():
    # Implemented in Fase 1 - Part 2 (S3 integration).
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Carga de exámenes se habilita en Parte 2 (integración S3)",
    )


@router.get("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def list_examenes():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Listado de exámenes se habilita en Parte 2",
    )
