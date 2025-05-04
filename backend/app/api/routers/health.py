from http import HTTPStatus

from fastapi import APIRouter

router = APIRouter()


@router.get("/check")
async def health():
    return {"status": HTTPStatus.OK.value}
