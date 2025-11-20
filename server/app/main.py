from fastapi import FastAPI, Depends
from .routers import images
from .internal import admin

app = FastAPI()

app.include_router(images.router)
app.include_router(
    admin.router,
    tags= ["admin"],
    responses={418: {"description": "I'm a teapot"}},
)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}