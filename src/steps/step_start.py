import streamlit as st
from utils.case_id import generate_case_id

def step_start():
    st.title("🏠 Energieausweis – Verbrauchsausweis")
    st.subheader("Geführte Erfassung")
    st.markdown("""
    In dieser geführten Erfassung erstellen Sie einen **Energieverbrauchsausweis**.
    Es werden folgende Daten benötigt:
    ✔ Postleitzahl des Gebäudes  
    ✔ Heizenergieverbräuche (mind. 3 Jahre)  
    ✔ Klimafaktoren (werden automatisch berücksichtigt)
    """)
    with st.form("start_form"):
        submit_btn = st.form_submit_button("📝 Erstelle Energieausweis")
    if submit_btn:
        st.session_state.case_id = generate_case_id()
        st.session_state.step = 1
        st.rerun()
