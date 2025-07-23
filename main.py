from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import AuthorizedSession
from fastapi import FastAPI
from vertexai.preview.language_models import ChatModel
import os, json
from google.protobuf import json_format
from google.cloud import aiplatform
from google.cloud import storage
import requests
# ─── Service Account & Dataset Listing ─────────────────────────────────────

# Path to your service account key
KEY_PATH = r"C:\\Users\\marco\\Downloads\\snapshot-api\\ai-patient-snapshot-001-6423a71a8f05.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

# Build the Healthcare API client
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
service = build("healthcare", "v1", credentials=credentials)
# List datasets in your project/region
project_id = "ai-patient-snapshot-001"
location   = "us-central1"
parent     = f"projects/{project_id}/locations/{location}"

datasets_response = service.projects().locations().datasets().list(parent=parent).execute()
#print("Datasets:", json.dumps(datasets_response, indent=2))

# ─── FHIR _search via raw HTTP ──────────────────────────────────────────────

# FHIR store identifiers
PROJECT        = project_id
LOCATION       = location
DATASET_ID     = "demo_central"
FHIR_STORE_ID  = "synthea"

FHIR_ROOT = (
    f"projects/{PROJECT}"
    f"/locations/{LOCATION}"
    f"/datasets/{DATASET_ID}"
    f"/fhirStores/{FHIR_STORE_ID}"
    f"/fhir"
)

# Prepare an authorized HTTP session
_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
_creds  = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=_scopes)
_session = AuthorizedSession(_creds)

dataset_name = f"projects/{project_id}/locations/{location}/datasets/{DATASET_ID}"

parent = f"projects/{project_id}/locations/{location}/datasets/{DATASET_ID}"

fhir_store = f"{parent}/fhirStores/{FHIR_STORE_ID}"
hc = service.projects() \
            .locations() \
            .datasets() \
            .fhirStores() \
            .fhir() 

# preguntarle a fernando que llaves de los diccionarios en arr son las que hay que usar

def collect(patient_id: str):
    client = storage.Client()
    bucket = client.bucket("bucket_marco_central")
    for blob in bucket.list_blobs():
      if patient_id in blob.name:
          ndjson_path = blob.name
          break
    blob = bucket.blob(ndjson_path)
    data = blob.download_as_text()
    result = {
        "Patient": None,
        "Observation": None,
        "MedicationRequest": None,
        "AllergyIntolerance": None,
        "DocumentReference": None,
        "ImagingStudy": None,
    }
    arr = ["Observation", "MedicationRequest", "AllergyIntolerance", "DocumentReference", "ImagingStudy"]
    # 3. Loop through each line, categorize, and collect
    c = 0
    for line in data.splitlines():
      if c == 0:
        result["Patient"] = line
        c += 1
      rec = json.loads(line)
      for i in arr:
        if i == rec["resourceType"]:
          if(i == "Observation" ):
            if "meta" in rec.keys():
              del rec["meta"]
            del rec["category"][0]["coding"][0]["system"]
            del rec["category"][0]["coding"][0]["display"]
            del rec['code']["coding"][0]["system"]
            result["Observation"] = rec
            
          
          elif i == "MedicationRequest":
            if "meta" in rec.keys():
              del rec["meta"]
            del rec["category"][0]["coding"][0]["system"]
            del rec["category"][0]['coding'][0]["display"]
            result["MedicationRequest"] = rec
          
          elif i == "AllergyIntolerance":
            if "meta" in rec.keys():
              del rec["meta"]
            del rec["clinicalStatus"]["coding"][0]["system"]
            del rec["verificationStatus"]["coding"][0]["system"]
            del rec['code']["coding"][0]["system"]
            del rec["code"]["coding"][0]["display"]
            result["AllergyIntolerance"] = rec
            
          elif i == "ImagingStudy":
            del rec["series"][0]["uid"]
            del rec["series"][0]["bodySite"]["system"]
            del rec["series"][0]["instance"][0]["sopClass"]["system"]
            del rec["series"][0]["instance"][0]["title"]
            result["ImagingStudy"] = rec
             
          elif i == "DocumentReference":
            del rec["meta"]
            del rec["identifier"]
            del rec["category"]
            del rec["type"]["coding"][0]["system"]
            del rec["author"][0]["display"]
            del rec["custodian"]["reference"]
            del rec["content"][0]["format"]["system"]
            del rec["content"][0]["format"]["display"]
            del rec["context"]["period"]["end"]
            result["DocumentReference"] = rec
          break
    return result
    
def summarize(fhir_bundle: dict) -> str:
  """
  Send the cleaned FHIR JSON to the Colab MedGemma endpoint
  and return its summary text.
  """
  COLAB_URL = "https://45f486b136c5.ngrok-free.app"  # <-- replace every time you restart Colab
  resp = requests.post(
    f"{COLAB_URL}/summarize",
    json={"fhir": fhir_bundle},
    timeout=100
  )
  resp.raise_for_status()
  return resp.json()["summary"]


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],           # or set to ["https://share.streamlit.io"]
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/snapshot/{pid}")
async def snapshot(pid: str):
    data    = collect(pid)
    summary = summarize(data)      # now `summary` is the string directly
    return {
        "patient_id": pid,
        "report":     summary
    }




if __name__ == "__main__":
    pid = "050b702e-a3bc-154d-4b3e-e0e6640a7869"
    data = collect(pid)
    report = summarize(data)
    print(report)

    


















































































