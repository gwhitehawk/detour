from flask import (Flask, render_template, request)
from urllib2 import (Request, urlopen)

from connections import get_connections


app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/request', methods=['POST'])
def search():
    response = get_connections(request.form['origin'], request.form['destination'], request.form['departureDate'], request.form['arrivalDate'])
    return render_template('request.html', data=response)


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
