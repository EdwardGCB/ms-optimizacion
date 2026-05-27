"""
Meta views
"""

from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/", summary="Service info")
def root():
    return {
        "service": "ms-products",
        "status": "running",
        "docs": "/docs#/"
    }


@router.get("/health", summary="Health check")
def health():
    return {
        "status": "OK"
    }
