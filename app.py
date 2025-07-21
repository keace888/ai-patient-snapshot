import streamlit as st
import requests

BACKEND = "https://ai-snapshot.loca.lt"  # your localtunnel URL

st.title("AI Patient Snapshot")
pid = st.text_input("Patient ID", "smart-123")

if st.button("Generate Snapshot"):
    try:
        resp = requests.get(f"{BACKEND}/snapshot/{pid}", timeout=300)
        resp.raise_for_status()
    except requests.RequestException as e:
        st.error(f"❌ Request failed: {e}")
    else:
        # Dump status & raw body so we can see what came back
        st.write("Status:", resp.status_code)
        st.write("Body:", resp.text)

        # Now try to parse JSON
        try:
            data = resp.json()
        except ValueError:
            st.error("❌ Response wasn’t valid JSON.")
        else:
            st.write("Parsed JSON:", data)
            if "report" in data:
                st.markdown(data["report"])
            else:
                st.error("❌ No `report` field in the response.")
