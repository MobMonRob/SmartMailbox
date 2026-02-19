from fastapi import FastAPI, Depends
from server.app.routers import images
import uvicorn

app = FastAPI()
app.include_router(images.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
