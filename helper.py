import requests
from flask import jsonify
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

headers = {'User-Agent': 'SmartMaps/1.0; kleines Projekt (kontakt: tbsunger@gmail.com)'}
session = requests.Session()
retries = Retry(total=3, connect=3, read=3,
                backoff_factor=1,
                status_forcelist=[429,500,502,503,504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def toISO(time):
  time = time[11:16] if time else '—'
  return time

@lru_cache(maxsize=256)
def findstopId(stopName):
  url = 'https://v6.vbb.transport.rest/locations'
  params = {
    'query': stopName,
  }
  
  response = session.get(url, params=params, headers=headers, timeout=10)
  print(f'StationID URL: {response.url}')
  data = response.json()
  return data[0]['id']