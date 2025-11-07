from fastapi import FastAPI
from app.database import engine, Base
from app.api import router

app = FastAPI()

app.include_router(router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
