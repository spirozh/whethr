# Import flask and template operators
from flask import Flask, render_template, redirect, flash, request, session

import requests, json
from . import config

# Define the WSGI application object
app = Flask(__name__)
app.config.from_object(config)


def api_call(url):
    """Make a GET call to a URL and return a parsed json object.

    """
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))


def loc_from_ip(ip):
    """Convert an IP address to a tuple containing latitude and
    longitude.

    Uses the IPstack web API to get the location

    """
    j = api_call(config.ip_api_url % ip)
    if j is not None:
        return j['latitude'], j['longitude']


def loc_from_placename(name):
    """Convert a placename to a tuple containing latitude and longitude.

    """
    j = api_call(config.li_api_search % name)
    if j is not None:
        return j[0]['lat'], j[0]['lon']


def placename_from_loc(loc):
    """Convert a tuple containing latitude and longitude to a placename.

    """
    lat, lon = loc
    j = api_call(config.li_api_reverse % (lat, lon))
    if j is not None:
        if 'city' in j['address']:
            return j['address']['city']
        else:
            return j['display_name']

        
def weather_for_loc(loc):
    """Get the weather for a location (passed in as a 2-ple containing
    latitude and longitude.

    Uses the OpenWeatherMap web service as an information source.

    """
    lat, lon = loc
    return api_call(config.owm_api_weather % (lat, lon))


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
    

def loc_from_args(args):
    """Get the location (a tuple of latitude and longitude) from the
    values in the args dictionary.

    There are three different ways to get the location:

    * location coordinates     (args.get['lat'] and args.get['lon'])
    * name of a location       (args.get['placename'])
    * ip address of the client (request.remote_addr)
    
    They are tried in that order and if the location can't be found,
    it is set to my house in Westmont.

    """
    
    loc = None

    lat = args.get('lat')
    lon = args.get('lon')
    if lat is not None and lon is not None:
        loc = lat, lon

    if loc is None:
        placename = args.get('placename')
        if placename is not None:
            loc = loc_from_placename(placename)
            if loc is None:
                flash("The location '%s' couldn't be found. I'll use my house as the location instead." % placename)

    if loc is None:
        ip = request.remote_addr
        loc = loc_from_ip(ip)
        
    loc = set_loc_to_home_if_invalid(loc)

    return loc

@app.route('/should_wear_a_hat', methods=['POST'])
def post_should_wear_a_hat_post():
    session['form'] = request.form
    return redirect('/should_wear_a_hat', code=302)

@app.route('/should_wear_a_hat', methods=['GET'])
def get_should_wear_a_hat():

    
    args = {}
    if 'form' in session:
        args = session['form'].copy()
        del session['form']
        
    loc = loc_from_args(args)
    weather = weather_for_loc(loc)

    placename = None
    if weather is not None:
        placename = weather['name']
    if placename is None:
        placename = placename_from_loc(loc)

    feels_like = round(weather['main']['feels_like'])
    is_cold = is_it_cold(weather)

    get_browser_pos = args is None

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
