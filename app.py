import streamlit as st
import requests

# Point this at your local FastAPI (or your ngrok/localtunnel URL if you still need it)
BACKEND =  "https://2fe36199aeca.ngrok-free.app"

st.title("AI Patient Snapshot")
pid = st.text_input("Patient ID", "smart-123")

if st.button("Generate Snapshot"):
    try:
        resp = requests.get(f"{BACKEND}/snapshot/{pid}", timeout=600)
        resp.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
    else:
        data = resp.json()  # { "patient_id": "...", "report": "…markdown here…" }
        report = data.get("report")
        if report:
            # Render exactly the markdown your LLM produced,
            # including headings, code fences, and lists
            st.markdown(report)
        else:
            st.error("No summary returned from the backend.")

