from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/snapshot/{patient_id}")
def get_snapshot(patient_id: str):
    return {"message": f"Snapshot for patient {patient_id}"}
