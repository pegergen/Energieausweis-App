# src/utils/db_helpers.py
import psycopg2
from typing import Dict, Optional

DB_NAME = "klimafaktoren"
DB_USER = "postgres"
DB_PASS = "N0nMeLacess1s"
DB_HOST = "localhost"

def get_klimafaktoren_for_plz(plz: str, start_daten: list[str]) -> Dict[str, float]:
    """
    Holt alle Klimafaktoren für die gegebene PLZ und eine Liste von Startdaten (YYYYMMDD).
    Gibt ein Dict zurück: {von_datum: klimafaktor}
    
    Args:
        plz: Postleitzahl als String
        start_daten: Liste von Datumsstrings im Format YYYYMMDD
        
    Returns:
        Dictionary mit {von_datum: klimafaktor} oder leeres Dict bei Fehler
        
    Example:
        >>> get_klimafaktoren_for_plz("82515", ["20220601", "20230601"])
        {"20220601": 1.05, "20230601": 1.03}
    """
    if not plz or not start_daten:
        return {}

    try:
        placeholders = ','.join(['%s'] * len(start_daten))  # %s,%s,%s...
        query = f"""
            SELECT von_datum, klimafaktor
            FROM klimafaktoren
            WHERE plz = %s AND von_datum IN ({placeholders});
        """
        params = [plz] + start_daten

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()

        # In dict umwandeln
        return {row[0]: row[1] for row in results}
    
    except Exception as e:
        print(f"❌ Datenbankfehler in get_klimafaktoren_for_plz: {e}")
        return {}


def get_klimafaktor_for_plz_single(plz: str, von_datum: str) -> Optional[float]:
    """
    Holt den Klimafaktor für eine PLZ und ein einzelnes Datum (YYYYMMDD).
    Praktische Wrapper-Funktion für Einzelabfragen.
    
    Args:
        plz: Postleitzahl als String
        von_datum: Datum als String im Format YYYYMMDD
        
    Returns:
        Klimafaktor als float oder None wenn nicht gefunden
        
    Example:
        >>> get_klimafaktor_for_plz_single("82515", "20220601")
        1.05
    """
    if not plz or not von_datum:
        return None
        
    result = get_klimafaktoren_for_plz(plz, [von_datum])
    return result.get(von_datum)