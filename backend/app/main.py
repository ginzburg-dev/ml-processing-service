from fastapi import FastAPI, Depends

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "ML Processing Service"}

@app.get("/api/health")
async def health():
    return {"ok": True}
