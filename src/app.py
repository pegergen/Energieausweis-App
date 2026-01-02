import streamlit as st
from steps.step_start import step_start
from steps.step_plz import step_plz
from steps.step_anlass import step_anlass
from steps.step_verbrauch import step_verbrauch
from utils.session import init_session_state


def main():
    init_session_state()

    step = st.session_state.step

    if step == 0:
        step_start()
    elif step == 1:
        step_plz()
    elif step == 2:
        step_anlass()
    elif step == 3:
        step_verbrauch()
    else:
        st.error("Unbekannter Schritt – Session zurückgesetzt.")
        st.session_state.step = 0


if __name__ == "__main__":
    main()
