# Import flask and template operators
from flask import Flask, render_template, redirect, flash, request
from pyowm import OWM
from ipstack import GeoLookup

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_pyfile('config.py')

# get the location from a query parameter (should be: "<lat>,<lon>")
def loc_from_query(where):
    (lat,lon) = where.split(',')
    return float(lat), float(lon)

# get the location related to an ip address
def loc_from_ip(ip):
    geo = GeoLookup(app.config['IPSTACK_KEY'])
    loc = geo.get_location(ip)
    return loc['latitude'], loc['longitude']

# ensure the location is valid
def ensure_valid_loc(loc):
    if loc[0] is None or loc[1] is None:
        return (33.9383776,-118.3111258)
        
    return loc

# get the weather for a given location
def weather_for_loc(loc):
    lat, lon = loc
    
    mgr = OWM(app.config['OWM_KEY']).weather_manager()
    observation = mgr.weather_at_coords(lat,lon)

    return observation.weather

# determine hat necessity given the weather
def a_hat_is_needed(weather):
    temp_feels_like = weather.temperature("fahrenheit")['feels_like']
    rain = weather.rain
    snow = weather.snow
    
    return (temp_feels_like < 60) or rain or snow


@app.route('/i_should_wear_a_hat')
def i_should_wear_a_hat():
    where = request.args.get('where')
    ip = request.remote_addr

    loc = loc_from_query(where) if where else loc_from_ip(ip)
    loc = ensure_valid_loc(loc)
    
    weather = weather_for_loc(loc)

    should = "should" if a_hat_is_needed(weather) else "should not"
    
    return render_template('i_should_wear_a_hat.html',
                           should=should, weather=weather), 200

@app.route('/')
def root():
    return redirect('/i_should_wear_a_hat', code=302)

# 404 errror handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
