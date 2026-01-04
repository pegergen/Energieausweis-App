# src/steps/step_anlass.py
from utils.helperfunctions import get_verbrauchsperioden
from utils.db_helpers import get_klimafaktoren_for_plz
import streamlit as st

def step_anlass():
    st.header("Schritt 2: Anlass & Objektinformationen")
    st.info(f"Aktuelle Case-ID: **{st.session_state.case_id}**")

    # Verbrauchsperioden abrufen
    perioden = get_verbrauchsperioden()

    # --- PLZ des Objekts schon aus SessionState holen (falls vorhanden) ---
    plz_objekt = st.session_state.get("plz_objekt", "")

    st.write("📅 Verbrauchsperioden für die Erfassung (Startdatum + Klimafaktor):")
    
    # Startdaten für DB-Abfrage vorbereiten
    start_daten = [start.strftime('%Y%m%d') for _, start, _ in perioden]

    klimafaktoren_dict = {}
    if plz_objekt and len(plz_objekt) == 5 and plz_objekt.isdigit():
        # Klimafaktoren aus der DB holen
        klimafaktoren_dict = get_klimafaktoren_for_plz(plz_objekt, start_daten)

    # Periodenliste mit Klimafaktoren anzeigen
    for label, start, ende in perioden:
        start_str = start.strftime('%Y%m%d')
        kf = klimafaktoren_dict.get(start_str, None)
        st.text(f"{start_str} | Klimafaktor: {kf if kf is not None else 'nicht verfügbar'}")
    
    with st.form("anlass_form"):
        # 1️⃣ Anlass
        anlass = st.radio(
            "Anlass für den Energieausweis",
            ["Vermietung", "Verkauf", "Sonstiges"],
            index=0
        )

        # 2️⃣ PLZ des Objekts
        plz_objekt_input = st.text_input(
            "PLZ des Objekts",
            value=plz_objekt,
            max_chars=5
        )

        # 3️⃣ Gebäudeart
        gebaeudeart = st.selectbox(
            "Gebäudeart",
            ["Einfamilienhaus", "Mehrfamilienhaus", "Gewerbeobjekt", "Sonstiges"],
            index=0
        )

        # 4️⃣ Baujahr
        baujahr = st.number_input(
            "Baujahr des Gebäudes",
            min_value=1800,
            max_value=2100,
            value=st.session_state.get("baujahr", 2000),
            step=1
        )

        # 5️⃣ Anzahl Wohnungen
        anzahl_wohnungen = st.number_input(
            "Anzahl Wohnungen",
            min_value=1,
            value=st.session_state.get("anzahl_wohnungen", 1),
            step=1
        )

        # 6️⃣ Gewerbe im Gebäude?
        gewerbe = st.radio(
            "Gewerbe im Gebäude?",
            ["Ja", "Nein"],
            index=0
        )

        # Buttons
        col_back, col_next = st.columns(2)
        with col_back:
            btn_back = st.form_submit_button("⬅ Zurück")
        with col_next:
            btn_next = st.form_submit_button("Weiter zu Verbrauchsdaten ➜")

    # -------------------------
    # Navigation & Validierung
    # -------------------------
    if btn_back:
        st.session_state.step = 1
        st.rerun()

    if btn_next:
        # Validierung PLZ
        if not plz_objekt_input or not plz_objekt_input.isdigit() or len(plz_objekt_input) != 5:
            st.warning("Bitte eine gültige 5-stellige PLZ des Objekts eingeben.")
        else:
            # Daten im Session State speichern
            st.session_state.anlass = anlass
            st.session_state.plz_objekt = plz_objekt_input
            st.session_state.gebaeudeart = gebaeudeart
            st.session_state.baujahr = baujahr
            st.session_state.anzahl_wohnungen = anzahl_wohnungen
            st.session_state.gewerbe = gewerbe

            st.session_state.step = 3
            st.rerun()
