from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import aiplatform
import vertexai, os, json
from dotenv import load_dotenv

# ─── Load your GCP credentials and settings ────────────────────────────────
load_dotenv()
PROJECT  = os.getenv("PROJECT_ID")  # e.g., ai-patient-snapshot-001
LOCATION = "us-central1"
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ENDPOINT_ID = "4705396294951108608"  # Your MedGemma one-click deployed endpoint

DATASET_ID     = "demo_central"  # FHIR dataset
FHIR_STORE_ID  = "synthea"
FHIR_ROOT      = (
    f"projects/{PROJECT}"
    f"/locations/{LOCATION}"
    f"/datasets/{DATASET_ID}"
    f"/fhirStores/{FHIR_STORE_ID}"
    f"/fhir"
)

# ─── Authenticate Google clients ────────────────────────────────────────────
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
hc = build("healthcare", "v1", credentials=credentials)
vertexai.init(project=PROJECT, location=LOCATION)
endpoint = aiplatform.Endpoint(endpoint_name=f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}")

# ─── Set up FastAPI app ────────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ─── FHIR patient data fetcher ─────────────────────────────────────────────
def collect(pid: str) -> dict:
    request = hc.projects().locations().datasets().fhirStores().fhir().search(
        parent=FHIR_ROOT,
        resourceType="Patient",
        body={
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [],
            "searchParams": {
                "_id": pid,
                "_include": [
                    "Observation:*",
                    "MedicationRequest:*",
                    "AllergyIntolerance:*",
                    "DocumentReference:*",
                    "ImagingStudy:*",
                ],
            },
        },
    )
    return request.execute()

# ─── Summarization using MedGemma deployed model ───────────────────────────
def summarize(evidence: dict) -> str:
    prompt = f"""
### Patient context
{json.dumps(evidence)[:8000]}

### Tasks
1. 120-word clinical summary.
2. Flag up to 3 immediate risks (JSON list).
3. Suggest next diagnostic or treatment steps.
"""
    response = endpoint.predict(
        instances=[{"prompt": prompt}],
        parameters={"temperature": 0.1}
    )
    return response.predictions[0]["content"]

# ─── API endpoint ───────────────────────────────────────────────────────────
@app.get("/snapshot/{pid}")
async def snapshot(pid: str):
    data   = collect(pid)
    report = summarize(data)
    return {"patient_id": pid, "report": report}

