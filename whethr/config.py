import os
from os.path import abspath, dirname

ENV = os.environ.get("ENV", "development")

# Statement for enabling the development environment
DEBUG = (ENV == "development")

# Define the application directory
BASE_DIR = abspath(dirname(__file__))

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection against *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data. 
CSRF_SESSION_KEY = "super_secret"

# Secret key for signing cookies
SECRET_KEY = "cookie_super_secret"

# API keys
OWM_KEY = "d5d1a49b1fdf3b6e04e1add6983ef4f7"
IPSTACK_KEY = "e54b84d449bb5f90092b0f575dd41fad"
LOCATIONIQ_KEY = "pk.ce1f8996f1bdbf6a99b21d1c611eb245"

# API urls
ip_api_url = f"http://api.ipstack.com/%s?access_key={IPSTACK_KEY}"
li_api_search = f"https://us1.locationiq.com/v1/search.php?key={LOCATIONIQ_KEY}&q=%s&format=json"
li_api_reverse = f"https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat=%s&lon=%s&zoom=14&format=json"
owm_api_weather = f"https://api.openweathermap.org/data/2.5/weather?appid={OWM_KEY}&lat=%s&lon=%s&units=imperial"
