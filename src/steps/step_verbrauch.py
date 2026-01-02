import streamlit as st
from datetime import date

# --- KONSTANTEN ---
ENERGIETRAEGER_MAP = {
    "Heizöl": "Liter",
    "Erdgas": "kWh",
    "Pellets": "kg",
    "Strom": "kWh",
    "Fernwärme": "kWh",
    "Sonstiges": "Einheit"
}

BRENNWERT_FAKTOREN = {
    "Heizöl": 10.6,
    "Erdgas": 1.0,
    "Pellets": 5.0,
    "Strom": 1.0,
    "Fernwärme": 1.0,
    "Sonstiges": 1.0
}

# --- HILFSFUNKTIONEN ---
def get_verbrauchsperioden():
    heute = date.today()
    ref_jahr = heute.year - 1 if heute.month < 6 else heute.year
    perioden = []
    for i in range(2, -1, -1):
        start = date(ref_jahr - i - 1, 6, 1)
        ende = date(ref_jahr - i, 5, 31)
        if ende > heute:
            ende = heute
        label = f"{start.strftime('%m.%Y')} - {ende.strftime('%m.%Y')}"
        perioden.append((label, start, ende))
    return perioden

# --- EDIT LOGIK ---
def edit_entry(idx, label, entry_idx):
    v = st.session_state.temp_perioden_data[label][entry_idx]

    st.session_state["edit_payload"] = {
        "idx": idx,
        "label": label,
        "entry_idx": entry_idx,
        "data": v,
    }

    st.session_state[f"edit_mode_{idx}"] = True

    st.rerun()

# Prefill bei Edit
if "edit_payload" in st.session_state:
    payload = st.session_state["edit_payload"]
    idx_edit = payload["idx"]
    v = payload["data"]

    st.session_state[f"datum_{idx_edit}"] = v["Datum"]
    st.session_state[f"et_{idx_edit}"] = v["Energieträger"]
    st.session_state[f"menge_{idx_edit}"] = v["Menge"]
    st.session_state[f"ww_{idx_edit}"] = v["Warmwasser"]

    st.session_state.pop("edit_payload")


# --- CALLBACK: SPEICHERN & RESET ---
def add_to_temp_and_reset(idx, label):
    datum = st.session_state[f"datum_{idx}"]
    et = st.session_state[f"et_{idx}"]
    menge = st.session_state[f"menge_{idx}"]
    ww = st.session_state[f"ww_{idx}"]
    
    is_pure_ww = (ww == "Nur Warmwasser-Verbrauch (keine Heizung)")
    
    ww_et, ww_menge = None, 0.0
    if ww == "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)":
        ww_et = st.session_state.get(f"ww_et_p_{idx}")
    elif ww in ["Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"]:
        ww_et = st.session_state.get(f"ww_et_s_{idx}")
        ww_menge = st.session_state.get(f"ww_menge_s_{idx}", 0.0)

    # kWh Umrechnung
    kwh_hz = menge * BRENNWERT_FAKTOREN.get(et, 1.0) if not is_pure_ww else 0.0
    kwh_ww = ww_menge * BRENNWERT_FAKTOREN.get(ww_et, 1.0) if ww_et in BRENNWERT_FAKTOREN else 0.0

    new_entry = {
        "Periode": label, "Datum": datum, 
        "Energieträger": "Keiner (reiner WW-Eintrag)" if is_pure_ww else et,
        "Menge": menge, "Einheit": ENERGIETRAEGER_MAP.get(et, ""), 
        "kWh_Heizung": round(kwh_hz, 2), "Warmwasser": ww,
        "Warmwasser_Energieart": ww_et, "Warmwasser_Menge_Separat": ww_menge,
        "Warmwasser_Einheit": ENERGIETRAEGER_MAP.get(ww_et, ""), "kWh_Warmwasser": round(kwh_ww, 2),
        "Leerstand": st.session_state.get(f"ls_val_{idx}", 0)
    }

    # --- Neu: Editieren statt append ---
    if st.session_state.get(f"edit_mode_{idx}", False):
        # Finde index des Eintrags, der bearbeitet wird
        for i, entry in enumerate(st.session_state.temp_perioden_data[label]):
            if entry["Datum"] == datum and entry["Energieträger"] == et:
                # Update bestehender Eintrag
                st.session_state.temp_perioden_data[label][i] = new_entry
                break
        else:
            # Falls kein passender Eintrag gefunden, hänge hinten an
            st.session_state.temp_perioden_data[label].append(new_entry)
    else:
        st.session_state.temp_perioden_data[label].append(new_entry)

    # Reset
    st.session_state[f"edit_mode_{idx}"] = False
    st.session_state[f"et_{idx}"] = "Bitte wählen..."
    st.session_state[f"menge_{idx}"] = 0.0
    st.session_state[f"ww_{idx}"] = "Bitte wählen..."


# --- HAUPTKOMPONENTE ---
def step_verbrauch():
    st.title("🌡 Energieausweis – Verbrauchserfassung")
    perioden = get_verbrauchsperioden()

    # Initialisierung, aber robust gegen Datumswechsel
    if "temp_perioden_data" not in st.session_state:
        st.session_state.temp_perioden_data = {}

    # fehlende Periodenlabels immer ergänzen
    for label, _, _ in perioden:
        st.session_state.temp_perioden_data.setdefault(label, [])

    
    tabs = st.tabs([f"📅 {p[0]}" for p in perioden])

    for idx, (label, start, ende) in enumerate(perioden):
        with tabs[idx]:
            # Initialisierung der State-Keys (verhindert Konflikte mit Widgets)
            if f"datum_{idx}" not in st.session_state: st.session_state[f"datum_{idx}"] = ende
            if f"et_{idx}" not in st.session_state: st.session_state[f"et_{idx}"] = "Bitte wählen..."
            if f"menge_{idx}" not in st.session_state: st.session_state[f"menge_{idx}"] = 0.0
            if f"ww_{idx}" not in st.session_state: st.session_state[f"ww_{idx}"] = "Bitte wählen..."
            if f"edit_mode_{idx}" not in st.session_state: st.session_state[f"edit_mode_{idx}"] = False

            # 1. LEERSTAND
            ls_key_internal = f"ls_val_{idx}"
            with st.container(border=True):
                st.markdown("🏠 **Gebäude-Leerstand**")
                leer_aktiv = st.checkbox(f"Leerstand für {label}?", key=f"leer_akt_{idx}")
                if leer_aktiv:
                    c_ls1, c_ls2 = st.columns(2)
                    monate = c_ls1.number_input("Monate Leerstand", 0, 12, key=f"ls_mon_{idx}")
                    fl_proz = c_ls2.number_input("Fläche (%)", 0, 100, 100, key=f"ls_fl_{idx}")
                    st.session_state[ls_key_internal] = round((monate / 12) * fl_proz, 1)
                else:
                    st.session_state[ls_key_internal] = 0

            # 2. EINGABEMASKE
            with st.container(border=True):
                if st.session_state[f"edit_mode_{idx}"]:
                    st.info("📝 **Bearbeitungsmodus aktiv:** Änderungen bitte mit Speichern bestätigen.")

                st.markdown("🔥 **Energieverbrauch hinzufügen**")
                
                # Widget-Parameter (Heizung deaktivieren wenn nur WW)
                haupt_dis = (st.session_state[f"ww_{idx}"] == "Nur Warmwasser-Verbrauch (keine Heizung)")
                einheit_hz = ENERGIETRAEGER_MAP.get(st.session_state[f"et_{idx}"], "Menge")

                c1, c2, c3 = st.columns([2,2,2])
                c1.date_input("Ablesedatum", key=f"datum_{idx}")
                
                et_options = ["Bitte wählen..."] + list(ENERGIETRAEGER_MAP.keys())
                c2.selectbox("Energieträger", et_options, key=f"et_{idx}", disabled=haupt_dis)
                c3.number_input(f"Menge ({einheit_hz})", min_value=0.0, step=0.1, key=f"menge_{idx}", disabled=haupt_dis)

                ww_opt = ["Bitte wählen...", "Ja", "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)", 
                          "Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"]
                st.selectbox("Warmwasser-Konfiguration", ww_opt, key=f"ww_{idx}")

                # Warmwasser-Untermenüs
                ww_sel = st.session_state[f"ww_{idx}"]
                if ww_sel == "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)":
                    st.selectbox("Energieart (Pauschale)", ["Bitte wählen...", "Strom", "Erdgas", "Heizöl"], key=f"ww_et_p_{idx}")
                elif ww_sel in ["Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"]:
                    st.caption("💧 Separater Warmwasser-Verbrauch:")
                    cw1, cw2 = st.columns(2)
                    cw1.selectbox("WW-Energieträger", et_options, key=f"ww_et_s_{idx}")
                    ww_einheit = ENERGIETRAEGER_MAP.get(st.session_state.get(f"ww_et_s_{idx}"), "Menge")
                    cw2.number_input(f"WW-Menge ({ww_einheit})", min_value=0.0, key=f"ww_menge_s_{idx}")

                # --- PLAUSIBILITÄTSPRÜFUNG ---
                valid = False
                if ww_sel == "Ja":
                    valid = (st.session_state[f"et_{idx}"] != "Bitte wählen..." and st.session_state[f"menge_{idx}"] > 0)
                elif ww_sel == "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)":
                    valid = (st.session_state[f"et_{idx}"] != "Bitte wählen..." and st.session_state[f"menge_{idx}"] > 0 and 
                             st.session_state.get(f"ww_et_p_{idx}") != "Bitte wählen...")
                elif ww_sel == "Nein, Verbrauch separat angeben":
                    valid = (st.session_state[f"et_{idx}"] != "Bitte wählen..." and st.session_state[f"menge_{idx}"] > 0 and 
                             st.session_state.get(f"ww_et_s_{idx}") != "Bitte wählen..." and st.session_state.get(f"ww_menge_s_{idx}", 0) > 0)
                elif ww_sel == "Nur Warmwasser-Verbrauch (keine Heizung)":
                    valid = (st.session_state.get(f"ww_et_s_{idx}") != "Bitte wählen..." and st.session_state.get(f"ww_menge_s_{idx}", 0) > 0)

                st.button("➕ In Liste vormerken", key=f"btn_add_{idx}", on_click=add_to_temp_and_reset, 
                          args=(idx, label), disabled=not valid, use_container_width=True)

            # 3. HISTORIE (SCROLLBAR)
            entries = st.session_state.temp_perioden_data.get(label, [])

            if entries:
                st.write("---")
                st.markdown(f"⏳ **Vorgemerkt für {label}:**")
                
                with st.container(height=300, border=False):
                    total_kwh = 0.0
                    for i, v in enumerate(st.session_state.temp_perioden_data[label]):
                        total_kwh += v['kWh_Heizung'] + v['kWh_Warmwasser']
                        cols = st.columns([6, 1, 1])
                        
                        if v['Warmwasser'] == "Nur Warmwasser-Verbrauch (keine Heizung)":
                            info = f"💧 **Reiner WW**: {v['Warmwasser_Menge_Separat']} {v['Warmwasser_Einheit']} (**{v['kWh_Warmwasser']} kWh**)"
                        else:
                            info = f"🔥 **{v['Energieträger']}**: {v['Menge']} {v['Einheit']}"
                            if v['Einheit'] != "kWh": info += f" (≙ **{v['kWh_Heizung']} kWh**)"
                            if v['kWh_Warmwasser'] > 0: info += f" | 💧 WW: {v['kWh_Warmwasser']} kWh"
                        
                        cols[0].info(info)
                        if cols[1].button("📝", key=f"ed_{idx}_{i}"): edit_entry(idx, label, i)
                        if cols[2].button("🗑", key=f"de_{idx}_{i}"):
                            st.session_state.temp_perioden_data[label].pop(i)
                            st.rerun()
                
                st.metric(f"Gesamtverbrauch {label}", f"{round(total_kwh, 1)} kWh")

    st.divider()
    if st.button("💾 Alle Daten final bestätigen", type="primary", use_container_width=True):
        st.success("Verbrauchsdaten wurden übernommen!")

if __name__ == "__main__":
    step_verbrauch()