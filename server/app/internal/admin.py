from fastapi import APIRouter

router = APIRouter()

@router.post("/admin")
async def update_admin():
    return {"message": "Admin getting schwifty"}