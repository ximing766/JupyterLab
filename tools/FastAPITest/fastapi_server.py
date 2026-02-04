
from fastapi import FastAPI

app = FastAPI()

@app.get("/process")
def process(data: str):
    return {"result": data.upper()}