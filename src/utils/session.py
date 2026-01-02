import streamlit as st

def init_session_state():
    defaults = {
        "step": 0,

        # Basisdaten
        "vorname": "",
        "name": "",
        "adresse": "",
        "plz": "",
        "ort": "",
        "mobil": "",
        "email": "",

        # finale gespeicherte Verbrauchsdaten
        "verbrauchsdaten": [],

        # temporäre periodenspezifische Eingaben
        "temp_perioden_data": {},

        # Fälle / IDs
        "generated_case_ids": [],
        "case_id": None,
    }

    # Initialisierung
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_all():
    """
    Kompletten Zustand zurücksetzen (praktisch für Entwicklung).
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
