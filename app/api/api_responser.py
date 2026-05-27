from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any, Optional


class ApiResponser:

    @staticmethod
    def success(
        data: Any = None,
        code: int = status.HTTP_200_OK,
        meta: Optional[dict] = None
    ) -> JSONResponse:

        payload = {
            "success": True,
            "data": data,
        }

        if meta:
            payload["meta"] = meta

        return JSONResponse(status_code=code, content=payload)

    @staticmethod
    def error(
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "ERROR",
        extra: Optional[dict] = None
    ) -> JSONResponse:

        payload = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            }
        }

        if extra:
            payload["error"]["extra"] = extra

        return JSONResponse(status_code=code, content=payload)
