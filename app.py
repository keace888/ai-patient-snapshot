import streamlit as st, requests
BACKEND="http://localhost:8000"
st.title("AI Patient Snapshot")
pid = st.text_input("Patient ID", "smart-123")
if st.button("Generate Snapshot"):
    r = requests.get(f"{BACKEND}/snapshot/{pid}").json()
    st.write(r)  # This will show the full response
    if "report" in r:
        st.markdown(r["report"])
    else:
        st.error("No 'report' field in backend response.")
