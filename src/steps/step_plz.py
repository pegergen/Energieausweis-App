import streamlit as st

def step_plz():
    st.header("Schritt 1: Kontakt- und Gebäudedaten")
    st.info(f"Aktuelle Case-ID: **{st.session_state.case_id}**")
    with st.form("plz_form"):
        col1, col2 = st.columns(2)
        vorname_in = col1.text_input("Vorname", value=st.session_state.vorname)
        name_in = col2.text_input("Nachname", value=st.session_state.name)

        adresse_in = st.text_input("Straße und Hausnummer", value=st.session_state.adresse)
        col_plz, col_ort = st.columns([1, 2])
        plz_in = col_plz.text_input("PLZ", value=st.session_state.plz, max_chars=5)
        ort_in = col_ort.text_input("Ort", value=st.session_state.ort)

        col3, col4 = st.columns(2)
        mobil_in = col3.text_input("Mobilnummer", value=st.session_state.mobil)
        email_in = col4.text_input("E-Mailadresse", value=st.session_state.email)

        submit_btn = st.form_submit_button("Weiter zu den Verbrauchsdaten ➜")

    if submit_btn:
        if not all([vorname_in, name_in, adresse_in, plz_in, ort_in, email_in]):
            st.error("Bitte füllen Sie alle Pflichtfelder aus.")
        elif not plz_in.isdigit() or len(plz_in) != 5:
            st.warning("Bitte eine gültige 5-stellige PLZ eingeben.")
        else:
            st.session_state.vorname = vorname_in
            st.session_state.name = name_in
            st.session_state.adresse = adresse_in
            st.session_state.plz = plz_in
            st.session_state.ort = ort_in
            st.session_state.mobil = mobil_in
            st.session_state.email = email_in
            st.session_state.step = 2
            st.rerun()
