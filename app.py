import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, render_template, request, jsonify
from urllib.parse import quote
from helper import toISO, findstopId

app = Flask(__name__)
headers = {'User-Agent': 'SmartMaps/1.0; kleines Projekt (kontakt: tbsunger@gmail.com)'}

session = requests.Session()
retries = Retry(total=3, connect=3, read=3,
                backoff_factor=1,
                status_forcelist=[429,500,502,503,504])
session.mount('https://', HTTPAdapter(max_retries=retries))

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/search')
def search():
  
  stationName = request.args.get('stationName', '')
  duration = request.args.get('duration', '30')
  
  stationId = findstopId(stationName)
  
  if not stationId:
    return jsonify([])
  
  url = f'https://v6.vbb.transport.rest/stops/{stationId}/departures'
  params = {
    'suburban': 'true',
    'subway': 'true',
    'tram': 'true',
    'bus': 'true',
    'ferry': 'false',
    'express': 'false',
    'regional': 'false',
    'duration': duration,
  }
  
  try:
    response = session.get(url, params=params, headers=headers,timeout=10)
    print(f'Abfahrten URL: {response.url}')
    data = response.json()
    
    departures = data.get('departures', [])
    
    for dep in departures:
      when = dep.get('when') or dep.get('plannedWhen')
      dep['time'] = toISO(when)
    
    return render_template('departures.html', departures=departures)
  except requests.exceptions.RequestException as e:
        print("VBB-Fehler:", repr(e))
        return jsonify({'error': 'API nicht erreichbar', 'detail': str(e)}), 500
  

@app.route('/map')
def map_view():
  trip_Id = request.args.get('trip', '')
  return render_template('map.html', trip_Id = trip_Id)


@app.route('/api/trip')
def api_trip():
  trip_id = request.args.get('trip', '')
  
  url = f"https://v6.vbb.transport.rest/trips/{quote(trip_id, safe='')}"

  response = session.get(url, params={'polyline':'true'}, headers=headers, timeout=10)
  print(f'Trip URL: {response.url}')
  trip = response.json()['trip']
  delay = 0
  stops = []
  for stopover in trip['stopovers']:
    if stopover['arrival'] is None:
      time = stopover['departure']
      time = toISO(time)
    else:
      time = stopover['arrival']
      time = toISO(time)
    
    stops.append({
      'name': stopover['stop']['name'],
      'coords': (
        stopover['stop']['location']['latitude'],
        stopover['stop']['location']['longitude'],
      ),
      'time': time,
    })
  
  if trip['arrivalDelay'] is not None and trip['arrivalDelay'] > 0:
    delay = trip['arrivalDelay']
    delay = delay / 60
  
  currentloc = []
  if 'currentLocation' in trip:
    currentlat = trip['currentLocation']['latitude']
    currentlon = trip['currentLocation']['longitude']
  
    currentloc.append({
      'coords':(
        currentlat,
        currentlon,
      )
    })

  punkte = [
    [f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]]
    for f in trip['polyline']['features']
  ]

  return jsonify({
    'punkte': punkte,
    'linie': trip['line']['name'],
    'richtung': trip.get('direction'),
    'stops': stops,
    'delay': delay,
    'currentloc': currentloc,
  })


if __name__ == '__main__':
  app.run(debug=True)