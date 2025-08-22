from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Busan Route API")
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Busan Route API is running"}
