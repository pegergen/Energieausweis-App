import streamlit as st
from utils.case_id import generate_case_id

def step_start():
    # Zentriertes Layout für einen "Landing-Page" Look
    st.markdown("<h1 style='text-align: center;'>🏠 Gebäude-Check</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Ihr Weg zum rechtssicheren Energieverbrauchsausweis</h3>", unsafe_allow_html=True)
    
    st.write("---")

    # Drei Spalten für die Highlights/Voraussetzungen
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📍 Standort")
        st.write("Eingabe der Postleitzahl zur regionalen Zuordnung.")
        
    with col2:
        st.markdown("### 📊 Daten")
        st.write("Heizverbräuche der letzten **3 Abrechnungsjahre**.")
        
    with col3:
        st.markdown("### ☁️ Klima")
        st.write("Automatische Bereinigung durch Klimafaktoren.")

    st.write("##") # Platzhalter

    # Container für die Aktionsbox
    with st.container(border=True):
        st.markdown("#### **Bereit für den Start?**")
        st.info("In den nächsten Schritten führen wir Sie durch die Erfassung. Ihre Daten werden sicher verarbeitet.")
        
        # Der Button wirkt besser, wenn er über die ganze Breite geht (use_container_width)
        if st.button("🚀 Jetzt Energieausweis erstellen", type="primary", use_container_width=True):
            st.session_state.case_id = generate_case_id()
            st.session_state.step = 1
            st.rerun()

    # Footer-Hinweis
    st.markdown("""
        <div style='text-align: center; font-size: 0.8em; color: gray; margin-top: 50px;'>
            Entspricht den aktuellen Anforderungen der GEG (Gebäudeenergiegesetz).
        </div>
    """, unsafe_allow_html=True)