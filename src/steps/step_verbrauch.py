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
    st.session_state[f"active_edit_idx_{idx}"] = entry_idx 
    st.rerun()

def cancel_edit(idx):
    st.session_state[f"edit_mode_{idx}"] = False
    st.session_state[f"active_edit_idx_{idx}"] = None
    st.session_state[f"et_{idx}"] = "Bitte wählen..."
    st.session_state[f"menge_{idx}"] = 0.0
    st.session_state[f"ww_{idx}"] = "Bitte wählen..."
    st.rerun()

# Prefill bei Edit
if "edit_payload" in st.session_state:
    p = st.session_state["edit_payload"]
    ix = p["idx"]
    v = p["data"]
    st.session_state[f"datum_{ix}"] = v["Datum"]
    st.session_state[f"et_{ix}"] = v["Energieträger"] if v["Energieträger"] != "Keiner (reiner WW-Eintrag)" else "Bitte wählen..."
    st.session_state[f"menge_{ix}"] = v["Menge"]
    st.session_state[f"ww_{ix}"] = v["Warmwasser"]
    st.session_state.pop("edit_payload")

# --- CALLBACK: SPEICHERN ---
def add_to_temp_and_reset(idx, label):
    d = st.session_state[f"datum_{idx}"]
    et = st.session_state[f"et_{idx}"]
    m = st.session_state[f"menge_{idx}"]
    ww = st.session_state[f"ww_{idx}"]
    is_pure_ww = (ww == "Nur Warmwasser-Verbrauch (keine Heizung)")
    
    ww_et, ww_m = None, 0.0
    if ww == "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)":
        ww_et = st.session_state.get(f"ww_et_p_{idx}")
    elif ww in ["Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"]:
        ww_et = st.session_state.get(f"ww_et_s_{idx}")
        ww_m = st.session_state.get(f"ww_menge_s_{idx}", 0.0)

    kwh_hz = m * BRENNWERT_FAKTOREN.get(et, 1.0) if not is_pure_ww else 0.0
    kwh_ww = ww_m * BRENNWERT_FAKTOREN.get(ww_et, 1.0) if ww_et in BRENNWERT_FAKTOREN else 0.0

    new_entry = {
        "Datum": d, "Energieträger": "Keiner (reiner WW-Eintrag)" if is_pure_ww else et,
        "Menge": m, "Einheit": ENERGIETRAEGER_MAP.get(et, ""), 
        "kWh_Heizung": round(kwh_hz, 2), "Warmwasser": ww,
        "Warmwasser_Energieart": ww_et, "Warmwasser_Menge_Separat": ww_m,
        "Warmwasser_Einheit": ENERGIETRAEGER_MAP.get(ww_et, ""), "kWh_Warmwasser": round(kwh_ww, 2)
    }

    edit_idx = st.session_state.get(f"active_edit_idx_{idx}")
    if st.session_state.get(f"edit_mode_{idx}", False) and edit_idx is not None:
        st.session_state.temp_perioden_data[label][edit_idx] = new_entry
    else:
        st.session_state.temp_perioden_data[label].append(new_entry)

    cancel_edit(idx)

# --- HAUPTFUNKTION ---
def step_verbrauch():
    st.title("🌡 Energieausweis – Verbrauchserfassung")
    perioden = get_verbrauchsperioden()

    # 1. Sicherstellen, dass die Grundstruktur im Session State existiert
    if "temp_perioden_data" not in st.session_state:
        st.session_state.temp_perioden_data = {}
    if "leerstand_data" not in st.session_state:
        st.session_state.leerstand_data = {}

    # 2. Sicherstellen, dass JEDES Label aus den Perioden einen Key hat (verhindert KeyError)
    for p in perioden:
        label = p[0]
        if label not in st.session_state.temp_perioden_data:
            st.session_state.temp_perioden_data[label] = []
        if label not in st.session_state.leerstand_data:
            st.session_state.leerstand_data[label] = {"monate": 0, "prozent": 100, "aktiv": False}

    tabs = st.tabs([f"📅 {p[0]}" for p in perioden])

    for idx, (label, start, ende) in enumerate(perioden):
        with tabs[idx]:
            # State Initialisierung
            if f"edit_mode_{idx}" not in st.session_state: st.session_state[f"edit_mode_{idx}"] = False

            # 1. LEERSTAND (Editierbar)
            with st.container(border=True):
                st.markdown("🏠 **Gebäude-Leerstand für diese Periode**")
                cfg = st.session_state.leerstand_data[label]
                leer_aktiv = st.checkbox("Leerstand vorhanden?", value=cfg["aktiv"], key=f"ls_chk_{idx}")
                st.session_state.leerstand_data[label]["aktiv"] = leer_aktiv
                
                if leer_aktiv:
                    c_ls1, c_ls2 = st.columns(2)
                    st.session_state.leerstand_data[label]["monate"] = c_ls1.number_input("Monate", 0, 12, value=cfg["monate"], key=f"ls_m_{idx}")
                    st.session_state.leerstand_data[label]["prozent"] = c_ls2.number_input("Fläche (%)", 0, 100, value=cfg["prozent"], key=f"ls_p_{idx}")

            # 2. EINGABEMASKE
            is_ed = st.session_state[f"edit_mode_{idx}"]
            with st.container(border=True):
                st.markdown("🔥 **Energieverbrauch hinzufügen**" if not is_ed else "📝 **Eintrag bearbeiten**")
                
                c1, c2, c3 = st.columns([2,2,2])
                c1.date_input("Ablesedatum", key=f"datum_{idx}")
                et_options = ["Bitte wählen..."] + list(ENERGIETRAEGER_MAP.keys())
                
                ww_sel = st.selectbox("Warmwasser-Konfiguration", ["Bitte wählen...", "Ja", "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)", "Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"], key=f"ww_{idx}")
                
                dis_hz = (ww_sel == "Nur Warmwasser-Verbrauch (keine Heizung)")
                c2.selectbox("Energieträger", et_options, key=f"et_{idx}", disabled=dis_hz)
                einheit_hz = ENERGIETRAEGER_MAP.get(st.session_state.get(f"et_{idx}"), "Einheit")
                c3.number_input(f"Menge ({einheit_hz})", min_value=0.0, step=0.1, key=f"menge_{idx}", disabled=dis_hz)

                if ww_sel == "Nein, die Warmwasserbereitung erfolgt separat (Pauschale)":
                    st.selectbox("Energieart (Pauschale)", ["Bitte wählen...", "Strom", "Erdgas", "Heizöl"], key=f"ww_et_p_{idx}")
                elif ww_sel in ["Nein, Verbrauch separat angeben", "Nur Warmwasser-Verbrauch (keine Heizung)"]:
                    cw1, cw2 = st.columns(2)
                    cw1.selectbox("WW-Energieträger", et_options, key=f"ww_et_s_{idx}")
                    ww_einheit = ENERGIETRAEGER_MAP.get(st.session_state.get(f"ww_et_s_{idx}"), "Einheit")
                    cw2.number_input(f"WW-Menge ({ww_einheit})", min_value=0.0, key=f"ww_menge_s_{idx}")

                # Validierung & Buttons
                btn_label = "💾 Änderungen speichern" if is_ed else "➕ In Liste vormerken"
                col_b1, col_b2 = st.columns([3,1] if is_ed else [1, 0.01])
                col_b1.button(btn_label, key=f"save_{idx}", on_click=add_to_temp_and_reset, args=(idx, label), type="primary")
                if is_ed: col_b2.button("✖", on_click=cancel_edit, args=(idx,), key=f"can_{idx}")

            # 3. HISTORIE (Die Liste)
            entries = st.session_state.temp_perioden_data.get(label, [])
            if entries:
                st.write("---")
                st.markdown(f"⏳ **Vorgemerkt für {label}:**")
                total_kwh = 0.0
                for i, v in enumerate(entries):
                    total_kwh += v['kWh_Heizung'] + v['kWh_Warmwasser']
                    cols = st.columns([6, 1, 1])
                    info = f"{v['Datum'].strftime('%d.%m.%Y')} | {v['Energieträger']}: {v['Menge']} {v['Einheit']} ({v['kWh_Heizung']} kWh)"
                    if v['kWh_Warmwasser'] > 0: info += f" + WW: {v['kWh_Warmwasser']} kWh"
                    cols[0].info(info)
                    if cols[1].button("📝", key=f"ed_{idx}_{i}"): edit_entry(idx, label, i)
                    if cols[2].button("🗑", key=f"del_{idx}_{i}"):
                        st.session_state.temp_perioden_data[label].pop(i)
                        st.rerun()
                
                # Zusammenfassung unten
                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Gesamtverbrauch", f"{round(total_kwh, 1)} kWh")
                l_cfg = st.session_state.leerstand_data[label]
                if l_cfg["aktiv"]:
                    m2.metric("Leerstand", f"{l_cfg['monate']} Mon. / {l_cfg['prozent']}%")
                else:
                    m2.metric("Leerstand", "Keiner")

    if st.button("💾 Alle Daten final bestätigen", type="primary", use_container_width=True):
        st.success("Daten erfolgreich übernommen!")

if __name__ == "__main__":
    step_verbrauch()