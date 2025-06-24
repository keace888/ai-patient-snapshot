import streamlit as st, requests
BACKEND="https://snapshot-api-657522101161.us-central1.run.app"
st.title("AI Patient Snapshot")
pid = st.text_input("Patient ID", "smart-123")
if st.button("Generate Snapshot"):
    r = requests.get(f"{BACKEND}/snapshot/{pid}").json()
    st.markdown(r["report"])
