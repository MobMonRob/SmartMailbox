from fastapi import UploadFile, APIRouter, Depends
from typing import Annotated

from ..dependencies import get_token

router = APIRouter(
    tags= ["images"],
    responses={404: {"description": "Not found"}},
)

@router.post("/images")
async def create_upload_file(file: UploadFile):
    return{"filename": file.filename}