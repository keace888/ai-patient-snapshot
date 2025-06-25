from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Path to your service account key
KEY_PATH = r"C:\Users\marco\Downloads\snapshot-api\ai-patient-snapshot-001-65959a4dade9.json"

# Set environment variable (optional if you use it below explicitly)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# Authenticate
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
service = build("healthcare", "v1", credentials=credentials)

# Example: List datasets
project_id = "ai-patient-snapshot-001"
location = "us-central1"  # or your region
parent = f"projects/{project_id}/locations/{location}"

response = service.projects().locations().datasets().list(parent=parent).execute()
print(response)


'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import healthcare_v1
from vertexai.language_models import ChatModel
import vertexai, os, json
from dotenv import load_dotenv

# ─── Load your GCP project ID from .env ──────────────────────────────────────
load_dotenv()  
PROJECT  = os.getenv("PROJECT_ID")                    # ai-patient-snapshot-001
LOCATION = "us-central1"                              # us-central1

# ─── Point at your FHIR store ───────────────────────────────────────────────
DATASET_ID     = "demo"                               # demo (FHIR dataset you created)
FHIR_STORE_ID  = "synthea"                            # synthea (FHIR store in that dataset)
FHIR_ROOT      = (
    f"projects/{PROJECT}"
    f"/locations/{LOCATION}"
    f"/datasets/{DATASET_ID}"
    f"/fhirStores/{FHIR_STORE_ID}"
    f"/fhir"
)

# ─── Initialize Google Healthcare & Vertex AI clients ───────────────────────
hc = healthcare_v1.FhirServiceClient()
vertexai.init(project=PROJECT, location=LOCATION)

# ─── Load the MedGemma text-27b chat model ──────────────────────────────────
gemma = ChatModel.from_pretrained("medgemma-text-27b").start_chat(temperature=0.1)

# ─── FastAPI app & CORS ─────────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def collect(pid: str) -> dict:
    bundle = hc.search(
        parent=FHIR_ROOT,
        resource_type="Patient",
        search_params={
            "_id": pid,
            "_include": [
                "Observation:*",
                "MedicationRequest:*",
                "AllergyIntolerance:*",
                "DocumentReference:*",
                "ImagingStudy:*",
            ],
        },
    )
    return healthcare_v1.json_format.MessageToDict(bundle)

def summarize(evidence: dict) -> str:
    prompt = f"""
### Patient context
{json.dumps(evidence)[:8000]}

### Tasks
1. 120-word clinical summary.
2. Flag up to 3 immediate risks (JSON list).
3. Suggest next diagnostic or treatment steps.
"""
    return gemma.send_message(prompt).text

@app.get("/snapshot/{pid}")
async def snapshot(pid: str):
    data   = collect(pid)
    report = summarize(data)
    return {"patient_id": pid, "report": report}
'''

