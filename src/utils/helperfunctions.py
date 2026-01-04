# src/utils/helperfunctions.py
from datetime import date

def get_verbrauchsperioden():
    """
    Liefert die letzten 3 Abrechnungszeiträume für den Energieverbrauch.
    Jeder Zeitraum läuft vom 01.06. eines Jahres bis 31.05. des Folgejahres.
    """
    heute = date.today()
    # Referenzjahr: wenn wir vor Juni sind, nimm Vorjahr
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
