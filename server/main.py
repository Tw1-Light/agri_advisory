from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server.config import SERVER_HOST, SERVER_PORT
from server.db.database import create_tables
from server.routers import advisory, demo, farm, sensors


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="AgriAdvisor Server", lifespan=lifespan)
app.include_router(farm.router)
app.include_router(sensors.router)
app.include_router(advisory.router)
app.include_router(demo.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("server.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
