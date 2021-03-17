# Import flask and template operators
from flask import Flask, render_template, redirect, flash, request

import requests, json
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
li_api_search = f"https://us1.locationiq.com/v1/search.php?key={config.LOCATIONIQ_KEY}&q=%s&format=json"
li_api_reverse = f"https://us1.locationiq.com/v1/reverse.php?key={config.LOCATIONIQ_KEY}&lat=%s&lon=%s&zoom=14&format=json"
owm_api_weather = f"https://api.openweathermap.org/data/2.5/weather?appid={config.OWM_KEY}&lat=%s&lon=%s&units=imperial"

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


def loc_from_placename(name):
    """Convert a placename to a tuple containing latitude and longitude.

    """
    response = requests.get(li_api_search % name)
    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        return j[0]['lat'], j[0]['lon']
    else:
        return None


def placename_from_loc(loc):
    """Convert a tuple containing latitude and longitude to a placename.

    """
    lat, lon = loc
    response = requests.get(li_api_reverse % (lat, lon))
    
    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        if 'city' in j['address']:
            return j['address']['city']
        else:
            return j['display_name']
    else:
        return None
 

def weather_for_loc(loc):
    """Get the weather for a location (passed in as a 2-ple containing
    latitude and longitude.

    Uses the OpenWeatherMap web service as an information source.

    """
    lat, lon = loc
    response = requests.get(owm_api_weather % (lat, lon))

    if response.status_code == 200:
        j = json.loads(response.content.decode('utf-8'))
        return j
    else:
        return None


def set_loc_to_home_if_invalid(loc):
    """If the location is not a 2 element tuple with both latitude
    and longitude set, then return a tuple with the latitude and
    longitude of my house.

    """
    if loc is not None:
        if isinstance(loc, tuple) and len(loc) == 2:
            if loc[0] is not None and loc[1] is not None:
                return loc

    return  33.9383776, -118.3111258 # my house

def is_it_cold(weather):
    """Decides if it cold enough for a hat.

    If the temperature is below 60F, it's considered cold.

    """
    temp_feels_like = weather['main']['feels_like']
    
    return temp_feels_like < 60
    

def loc_from_request():
    """Get the location (a tuple of latitude and longitude) from the
    values in the request.

    There are three different ways to get the location, the lat and
    lon query parameters, the name of a location, and the ip address
    of the client.  They are tried in that order and if the location
    can't be found by those means, it is set to my house in Westmont.

    """
    
    loc = None

    args = request.form
    lat = args.get('lat')
    lon = args.get('lon')
    if lat is not None and lon is not None:
        loc = loc_from_strings(lat, lon)

    if loc is None:
        placename = args.get('placename')
        if placename is not None:
            loc = loc_from_placename(placename)
            if loc is None:
                flash("'%s' cannot be located." % placename)

    if loc is None:
        ip = request.remote_addr
        loc = loc_from_ip(ip)
        
    loc = set_loc_to_home_if_invalid(loc)

    return loc

@app.route('/should_wear_a_hat', methods=['GET', 'POST'])
def should_wear_a_hat():

    loc = loc_from_request()
    weather = weather_for_loc(loc)

    placename = None
    if weather is not None:
        placename = weather['name']
    if placename is None:
        placename = placename_from_loc(loc)

    feels_like = round(weather['main']['feels_like'])
    is_cold = is_it_cold(weather)

    args = request.form
    get_browser_pos = args.get('lat') is None and args.get('placename') is None

    return render_template('should_wear_a_hat.html',
                           placename = placename,
                           feels_like = feels_like,
                           is_cold = is_cold,
                           weather = weather,
                           get_browser_pos = get_browser_pos), 200

@app.route('/')
def root():
    return redirect('/should_wear_a_hat', code=302)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404
