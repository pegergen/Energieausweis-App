import streamlit as st
from datetime import date

# --- KONSTANTEN ---
ENERGIETRAEGER_MAP = {
    "Heizöl": "Liter", "Erdgas": "kWh", "Pellets": "kg",
    "Strom": "kWh", "Fernwärme": "kWh", "Sonstiges": "Einheit"
}

BRENNWERT_FAKTOREN = {
    "Heizöl": 10.6, "Erdgas": 1.0, "Pellets": 5.0,
    "Strom": 1.0, "Fernwärme": 1.0, "Sonstiges": 1.0
}

# Warmwasser-Optionen als Konstanten (verhindert Tippfehler)
NICHT_AUSGEWAEHLT = "Bitte wählen..."
WW_INKLUSIVE = "Ja, inklusive"
WW_PAUSCHALE = "Nein, Pauschale"
WW_SEPARAT = "Nein, separat"
WW_NUR = "Nur Warmwasser-Verbrauch (keine Heizung)"

WW_OPTIONEN = [NICHT_AUSGEWAEHLT, WW_INKLUSIVE, WW_PAUSCHALE, WW_SEPARAT, WW_NUR]

# --- HILFSFUNKTIONEN ---
from utils.helperfunctions import get_verbrauchsperioden

# Klimafaktor-Import mit detailliertem Debugging
KLIMAFAKTOR_AVAILABLE = False  # WICHTIG: Immer vorher definieren!

try:
    from utils.db_helpers import get_klimafaktoren_for_plz
    KLIMAFAKTOR_AVAILABLE = True
    print("✅ get_klimafaktoren_for_plz erfolgreich importiert")
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    def get_klimafaktoren_for_plz(plz, start_daten):
        """Fallback-Funktion falls Import fehlschlägt"""
        return {}
except AttributeError as e:
    print(f"❌ Funktion existiert nicht in db_helpers.py: {e}")
    def get_klimafaktoren_for_plz(plz, start_daten):
        """Fallback-Funktion falls Funktion nicht existiert"""
        return {}
except Exception as e:
    print(f"❌ Unerwarteter Fehler beim Import: {type(e).__name__}: {e}")
    def get_klimafaktoren_for_plz(plz, start_daten):
        """Fallback-Funktion bei sonstigen Fehlern"""
        return {}

def format_entry_display(v):
    """Formatiert einen Verbrauchseintrag für die Historie-Anzeige."""
    info = f"**{v['Datum'].strftime('%d.%m.%Y')}** | "
    
    if v['Warmwasser'] == WW_NUR:
        # Reiner WW-Eintrag
        info += (f"💧 Reiner WW-Eintrag ({v['Warmwasser_Energieart']}): "
                f"{v['Warmwasser_Menge_Separat']} {v['Warmwasser_Einheit']} "
                f"({v['kWh_Warmwasser']} kWh)")
    else:
        # Standard-Eintrag mit Heizung
        if v['Energieträger'] != "Keiner (reiner WW-Eintrag)":
            info += (f"🔥 {v['Energieträger']}: {v['Menge']} {v['Einheit']} "
                    f"({v['kWh_Heizung']} kWh)")
        
        # Warmwasser-Zusätze
        if v['Warmwasser'] == WW_INKLUSIVE:
            info += " (💧 WW inklusiv)"
        elif v['Warmwasser'] == WW_SEPARAT:
            info += (f" + 💧 WW ({v['Warmwasser_Energieart']}): "
                    f"{v['Warmwasser_Menge_Separat']} {v['Warmwasser_Einheit']} "
                    f"({v['kWh_Warmwasser']} kWh)")
        elif v['Warmwasser'] == WW_PAUSCHALE:
            info += f" + 💧 WW (Pauschale {v['Warmwasser_Energieart']})"
    
    return info

# --- LOGIK FUNKTIONEN (CALLBACKS) ---
def prepare_edit(idx, label, entry_idx):
    """Befüllt die Eingabemaske mit Daten aus einem bestehenden Eintrag."""
    v = st.session_state.temp_perioden_data[label][entry_idx]
    
    # Widget-Keys im State setzen (muss im Callback passieren!)
    st.session_state[f"datum_{idx}"] = v["Datum"]
    st.session_state[f"et_{idx}"] = v["Energieträger"] if v["Energieträger"] != "Keiner (reiner WW-Eintrag)" else NICHT_AUSGEWAEHLT
    st.session_state[f"menge_{idx}"] = v["Menge"]
    st.session_state[f"ww_{idx}"] = v["Warmwasser"]
    
    if v.get("Warmwasser_Energieart"):
        if v["Warmwasser"] == WW_PAUSCHALE:
            st.session_state[f"ww_et_p_{idx}"] = v["Warmwasser_Energieart"]
        else:
            st.session_state[f"ww_et_s_{idx}"] = v["Warmwasser_Energieart"]
            st.session_state[f"ww_menge_s_{idx}"] = v["Warmwasser_Menge_Separat"]

    st.session_state[f"edit_mode_{idx}"] = True
    st.session_state[f"active_edit_idx_{idx}"] = entry_idx

def cancel_edit(idx):
    """Setzt die Eingabemaske zurück."""
    st.session_state[f"edit_mode_{idx}"] = False
    st.session_state[f"active_edit_idx_{idx}"] = None
    st.session_state[f"et_{idx}"] = NICHT_AUSGEWAEHLT
    st.session_state[f"menge_{idx}"] = 0.0
    st.session_state[f"ww_{idx}"] = NICHT_AUSGEWAEHLT

def handle_ww_change(idx):
    """Setzt Heizungs-Felder zurück, wenn nur WW gewählt wurde."""
    if st.session_state[f"ww_{idx}"] == WW_NUR:
        st.session_state[f"et_{idx}"] = NICHT_AUSGEWAEHLT
        st.session_state[f"menge_{idx}"] = 0.0

def add_to_temp_and_reset(idx, label):
    """Speichert oder aktualisiert den Eintrag nach Validierung."""
    d = st.session_state[f"datum_{idx}"]
    et = st.session_state[f"et_{idx}"]
    m = st.session_state[f"menge_{idx}"]
    ww = st.session_state[f"ww_{idx}"]
    is_pure_ww = (ww == WW_NUR)
    
    # ===== VALIDIERUNG =====
    # 1. Warmwasser-Konfiguration muss gewählt sein
    if ww == NICHT_AUSGEWAEHLT:
        st.session_state[f"error_msg_{idx}"] = "⚠️ Bitte wähle eine Warmwasser-Konfiguration."
        return
    
    # 2. Bei Heizungs-Einträgen: Energieträger und Menge prüfen
    if not is_pure_ww:
        if et == NICHT_AUSGEWAEHLT:
            st.session_state[f"error_msg_{idx}"] = "⚠️ Bitte wähle einen Energieträger für die Heizung."
            return
        if m <= 0:
            st.session_state[f"error_msg_{idx}"] = "⚠️ Die Heizungs-Menge muss größer als 0 sein."
            return
    
    ww_et, ww_m = None, 0.0
    
    # 3. Warmwasser-Daten sammeln und validieren
    if ww == WW_PAUSCHALE:
        ww_et = st.session_state.get(f"ww_et_p_{idx}")
        if not ww_et or ww_et == NICHT_AUSGEWAEHLT:
            st.session_state[f"error_msg_{idx}"] = "⚠️ Bitte wähle eine Energieart für die WW-Pauschale."
            return
            
    elif ww in [WW_SEPARAT, WW_NUR]:
        ww_et = st.session_state.get(f"ww_et_s_{idx}")
        ww_m = st.session_state.get(f"ww_menge_s_{idx}", 0.0)
        
        if not ww_et or ww_et == NICHT_AUSGEWAEHLT:
            st.session_state[f"error_msg_{idx}"] = "⚠️ Bitte wähle einen Energieträger für Warmwasser."
            return
        if ww_m <= 0:
            st.session_state[f"error_msg_{idx}"] = "⚠️ Die Warmwasser-Menge muss größer als 0 sein."
            return

    # ===== BERECHNUNG =====
    kwh_hz = m * BRENNWERT_FAKTOREN.get(et, 1.0) if not is_pure_ww else 0.0
    kwh_ww = ww_m * BRENNWERT_FAKTOREN.get(ww_et, 1.0) if ww_et in BRENNWERT_FAKTOREN else 0.0

    new_entry = {
        "Datum": d, 
        "Energieträger": "Keiner (reiner WW-Eintrag)" if is_pure_ww else et,
        "Menge": m, 
        "Einheit": ENERGIETRAEGER_MAP.get(et, ""), 
        "kWh_Heizung": round(kwh_hz, 2), 
        "Warmwasser": ww,
        "Warmwasser_Energieart": ww_et, 
        "Warmwasser_Menge_Separat": ww_m,
        "Warmwasser_Einheit": ENERGIETRAEGER_MAP.get(ww_et, ""), 
        "kWh_Warmwasser": round(kwh_ww, 2)
    }

    # ===== SPEICHERN =====
    edit_idx = st.session_state.get(f"active_edit_idx_{idx}")
    if st.session_state.get(f"edit_mode_{idx}", False) and edit_idx is not None:
        st.session_state.temp_perioden_data[label][edit_idx] = new_entry
        st.session_state[f"success_msg_{idx}"] = "✅ Eintrag erfolgreich aktualisiert!"
    else:
        st.session_state.temp_perioden_data[label].append(new_entry)
        st.session_state[f"success_msg_{idx}"] = "✅ Eintrag erfolgreich hinzugefügt!"

    # Fehlermeldung löschen bei Erfolg
    st.session_state[f"error_msg_{idx}"] = None
    cancel_edit(idx)

# --- HAUPTFUNKTION ---
def step_verbrauch():
    st.title("🌡 Energieausweis – Verbrauchserfassung")
    
    # Debug-Info (kann später entfernt werden)
    if not KLIMAFAKTOR_AVAILABLE:
        st.warning("⚠️ Klimafaktor-Feature nicht verfügbar. Prüfe ob die Funktion `get_klimafaktoren_for_plz` in `utils/db_helpers.py` existiert.")
    
    perioden = get_verbrauchsperioden()

    # Initialisierung Session State
    if "temp_perioden_data" not in st.session_state: st.session_state.temp_perioden_data = {}
    if "leerstand_data" not in st.session_state: st.session_state.leerstand_data = {}

    for p in perioden:
        label = p[0]
        if label not in st.session_state.temp_perioden_data: st.session_state.temp_perioden_data[label] = []
        if label not in st.session_state.leerstand_data:
            st.session_state.leerstand_data[label] = {"monate": 0, "prozent": 100, "aktiv": False}

    tabs = st.tabs([f"📅 {p[0]}" for p in perioden])

    for idx, (label, start, ende) in enumerate(perioden):
        with tabs[idx]:
            # Klimafaktor aus DB abrufen, falls PLZ gesetzt ist UND Funktion verfügbar
            if KLIMAFAKTOR_AVAILABLE:
                plz_objekt = st.session_state.get("plz_objekt")
                if plz_objekt:
                    von_datum_str = start.strftime('%Y%m%d')
                    try:
                        # Funktion erwartet eine LISTE von Daten, also übergeben wir [von_datum_str]
                        result = get_klimafaktoren_for_plz(plz_objekt, [von_datum_str])
                        kf = result.get(von_datum_str) if result else None
                        
                        if kf is not None:
                            st.info(f"🌡 Klimafaktor für PLZ {plz_objekt}, Start {von_datum_str}: **{kf}**")
                        else:
                            st.warning(f"⚠️ Kein Klimafaktor für PLZ {plz_objekt} und Start {von_datum_str} gefunden.")
                    except Exception as e:
                        st.error(f"❌ Fehler beim Abrufen des Klimafaktors: {type(e).__name__}: {e}")
            
            if f"edit_mode_{idx}" not in st.session_state: st.session_state[f"edit_mode_{idx}"] = False
            is_ed = st.session_state[f"edit_mode_{idx}"]

            # 1. LEERSTAND (Gilt für das Abrechnungsjahr)
            with st.container(border=True):
                st.markdown("🏠 **Gebäude-Leerstand**")
                cfg = st.session_state.leerstand_data[label]
                leer_aktiv = st.checkbox("Leerstand vorhanden?", value=cfg["aktiv"], key=f"ls_chk_{idx}")
                st.session_state.leerstand_data[label]["aktiv"] = leer_aktiv
                
                if leer_aktiv:
                    c_ls1, c_ls2 = st.columns(2)
                    st.session_state.leerstand_data[label]["monate"] = c_ls1.number_input("Monate", 0, 12, value=cfg["monate"], key=f"ls_m_{idx}")
                    st.session_state.leerstand_data[label]["prozent"] = c_ls2.number_input("Fläche (%)", 0, 100, value=cfg["prozent"], key=f"ls_p_{idx}")

            # 2. EINGABEMASKE
            with st.container(border=True):
                st.markdown("🔥 **Energieverbrauch hinzufügen**" if not is_ed else "📝 **Eintrag bearbeiten**")
                
                # Fehler- und Erfolgsmeldungen anzeigen
                if f"error_msg_{idx}" in st.session_state and st.session_state[f"error_msg_{idx}"]:
                    st.error(st.session_state[f"error_msg_{idx}"])
                if f"success_msg_{idx}" in st.session_state and st.session_state[f"success_msg_{idx}"]:
                    st.success(st.session_state[f"success_msg_{idx}"])
                    # Erfolg nach Anzeige löschen
                    st.session_state[f"success_msg_{idx}"] = None
                
                c1, c2, c3 = st.columns([2,2,2])
                c1.date_input("Ablesedatum", key=f"datum_{idx}", min_value=start, max_value=ende)
                
                # Energieträger zuerst
                et_options = [NICHT_AUSGEWAEHLT] + list(ENERGIETRAEGER_MAP.keys())
                c2.selectbox("Energieträger", et_options, key=f"et_{idx}")
                
                # Warmwasser-Konfiguration danach
                ww_sel = c3.selectbox(
                    "Warmwasser-Konfiguration", 
                    WW_OPTIONEN, 
                    key=f"ww_{idx}",
                    on_change=handle_ww_change,
                    args=(idx,)
                )
                
                dis_hz = (ww_sel == WW_NUR)
                einheit_hz = ENERGIETRAEGER_MAP.get(st.session_state.get(f"et_{idx}"), "Einheit")
                c3.number_input(f"Menge ({einheit_hz})", min_value=0.0, step=0.1, key=f"menge_{idx}", disabled=dis_hz)

                # Dynamische WW-Felder
                if ww_sel == WW_PAUSCHALE:
                    st.selectbox("Energieart (WW-Pauschale)", [NICHT_AUSGEWAEHLT, "Strom", "Erdgas", "Heizöl"], key=f"ww_et_p_{idx}")
                elif ww_sel in [WW_SEPARAT, WW_NUR]:
                    cw1, cw2 = st.columns(2)
                    cw1.selectbox("WW-Energieträger", et_options, key=f"ww_et_s_{idx}")
                    ww_ein = ENERGIETRAEGER_MAP.get(st.session_state.get(f"ww_et_s_{idx}"), "Einheit")
                    cw2.number_input(f"WW-Menge ({ww_ein})", min_value=0.0, key=f"ww_menge_s_{idx}")

                # Buttons
                col_b1, col_b2 = st.columns([3, 1] if is_ed else [1, 0.01])
                col_b1.button("💾 Speichern" if is_ed else "➕ Vormerken", key=f"save_{idx}", on_click=add_to_temp_and_reset, args=(idx, label), type="primary", use_container_width=True)
                if is_ed:
                    col_b2.button("✖", on_click=cancel_edit, args=(idx,), key=f"can_{idx}", use_container_width=True)

            # 3. HISTORIE & ZUSAMMENFASSUNG
            entries = st.session_state.temp_perioden_data.get(label, [])
            if entries:
                st.write("---")
                st.markdown(f"⏳ **Vorgemerkt für {label}:**")
                total_kwh = 0.0
                for i, v in enumerate(entries):
                    total_kwh += v['kWh_Heizung'] + v['kWh_Warmwasser']
                    cols = st.columns([6, 1, 1])
                    
                    # Formatierte Anzeige mit ausgelagerter Funktion
                    cols[0].info(format_entry_display(v))
                    
                    # Buttons
                    cols[1].button("📝", key=f"ed_{idx}_{i}", on_click=prepare_edit, args=(idx, label, i))
                    if cols[2].button("🗑", key=f"del_{idx}_{i}"):
                        st.session_state.temp_perioden_data[label].pop(i)
                        st.rerun()
                
                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Gesamtverbrauch", f"{round(total_kwh, 1)} kWh")
                l_cfg = st.session_state.leerstand_data[label]
                m2.metric("Leerstand", f"{l_cfg['monate']} Mon. / {l_cfg['prozent']}%" if l_cfg["aktiv"] else "Keiner")

    if st.button("💾 Alle Daten final bestätigen", type="primary", use_container_width=True):
        st.success("Verbrauchsdaten für alle Zeiträume wurden gespeichert.")
        
    # --- Navigation ---
    st.write("---")
    col_nav1, col_nav2 = st.columns(2)

    with col_nav1:
        if st.button("⬅ Zurück", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with col_nav2:
        if st.button("Weiter zum PDF-Export ➡", type="primary", use_container_width=True):
            if any(st.session_state.temp_perioden_data.values()):
                st.session_state.step = 4
                st.rerun()
            else:
                st.warning("Bitte erfasse mindestens einen Verbrauchs-Eintrag, um fortzufahren.")        

if __name__ == "__main__":
    step_verbrauch()