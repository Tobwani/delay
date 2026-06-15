import requests

BASE = "https://v6.vbb.transport.rest"

def stop_id(name):
    """Wandelt einen Stationsnamen in seine VBB-ID um."""
    r = requests.get(f"{BASE}/locations", params={
        "query": name,
        "results": 1,
        "poi": "false",        # keine POIs
        "addresses": "false",  # keine Adressen, nur Haltestellen
    })
    return r.json()[0]["id"]

# IDs auflösen
von = stop_id("U Hönow")
nach = stop_id("S Schönhauser Allee")
via = stop_id("U Hellersdorf")

# Journey suchen
r = requests.get(f"{BASE}/journeys", params={
    "from": von,
    "to": nach,
    "via": via,           # erzwingt den Zwischenstopp
    "results": 1,
    "stopovers": "true",  # alle Halte unterwegs mitliefern
})

journey = r.json()["journeys"][0]


for leg in journey["legs"]:
    if leg.get("walking"):
        print(f"🚶 Fußweg → {leg['destination']['name']}")
    else:
        line = leg["line"]["name"]
        print(f"{line}: {leg['origin']['name']} → {leg['destination']['name']}")
        print(f"   ab {leg['departure']}  an {leg['arrival']}")