# Import flask and template operators
from flask import Flask, render_template, redirect, flash, request

import requests, json

from ipstack import GeoLookup

from .exceptions import *

from . import config

# Define the WSGI application object
app = Flask(__name__)
app.config.from_object(config)

 


def loc_from_strings(lat, lon):
    """Converts the latitude and longitude parameters to a tuple
    containing latitude and longitude as floats.

    """
    return float(lat), float(lon)


ip_api_url = f"http://api.ipstack.com/%s?access_key={config.IPSTACK_KEY}"
def loc_from_ip(ip):
    """Convert an IP address to a tuple containing latitude and
    longitude.

    Uses the IPstack web API to get the location

    """
    response = requests.get(ip_api_url % ip)
    if response.status_code == 200:
        loc = json.loads(response.content.decode('utf-8'))
        return loc['latitude'], loc['longitude']
    else:
        return None


li_api_urlbase = f"https://us1.locationiq.com/v1/%s.php?key={config.LOCATIONIQ_KEY}"

li_api_search = f"{(li_api_urlbase % 'search')}&q=%s&format=json"
def loc_from_placename(name):
    """Convert a placename to a tuple containing latitude and longitude.

    Raises an UnknownLocationError if a location cannot be found that
    matches the name.
    """
    response = requests.get(li_api_search % name)
    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        return j[0]['lat'], j[0]['lon']
    else:
        return None

li_api_reverse = f"{(li_api_urlbase % 'reverse')}&lat=%s&lon=%s&format=json&zoom=14"
def placename_from_loc(loc):
    lat, lon = loc
    response = requests.get(li_api_reverse % (lat, lon))
    
    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        return j['display_name']
    else:
        return None
 

owm_api_urlbase = f"https://api.openweathermap.org/data/2.5/weather?appid={config.OWM_KEY}"
owm_api_url = f"{owm_api_urlbase}&lat=%s&lon=%s&units=imperial"
def weather_for_loc(loc):
    """Get the weather for a location (passed in as a 2-ple containing
    latitude and longitude.

    Uses the OpenWeatherMap web service as an information source.

    """
    lat, lon = loc
    response = requests.get(owm_api_url % (lat, lon))

    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        return j
    else:
        return None


# ensure the location is valid
def ensure_valid_loc(loc):
    """Ensures a location tuple is a 2 element tuple and has both latitude
    and longitude.

    If either is missing, then replace them both with the latitude and
    longitude of my house.

    """
    lat, lon = False, False
    if isinstance(loc, tuple) and len(loc) == 2:
        lat, lon = loc
    
    if not lat or not lon:
        lat, lon = 33.9383776, -118.3111258 # my house

    return lat, lon



def is_it_cold(weather):
    """Decides if it cold enough for a hat.

    If the temperature is below 60F, it's considered cold.

    """
    temp_feels_like = weather['main']['feels_like']
    
    return temp_feels_like < 60
    

@app.route('/should_wear_a_hat')
def should_wear_a_hat():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    name = request.args.get('name')
    ip = request.remote_addr

    loc = None
    if lat and lon:
        loc = loc_from_strings(lat, lon)
    elif name:
        try:
            loc = loc_from_placename(name)
        except UnknownLocationError:
            msg = "'%s' cannot be located."
            flash(msg % name)

    else:
        loc = loc_from_ip(ip)
        
    loc = ensure_valid_loc(loc)
    weather = weather_for_loc(loc)
    name = weather['name']
    if not name:
        name = placename_from_loc(loc)

    feels_like = round(weather['main']['feels_like'])
    is_cold = is_it_cold(weather)

    
    return render_template('should_wear_a_hat.html',
                           placename = name,
                           is_cold = is_cold,
                           feels_like = feels_like,
                           weather = weather), 200

@app.route('/')
def root():
    return redirect('/should_wear_a_hat', code=302)

# 404 errror handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404
