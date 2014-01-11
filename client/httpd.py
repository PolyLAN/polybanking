from flask import Flask
from flask import render_template
from flask import request

import config
from libs.polybanking import PolyBanking

import uuid

api = PolyBanking(config.POLYBANKING_SERVER, config.CONFIG_ID, config.KEY_REQUESTS, config.KEY_IPN, config.KEY_API)

app = Flask(__name__)


@app.route("/")
def home():
    """Display the home page"""
    return render_template('home.html')


@app.route('/start')
def start():
    """Start a new paiement"""

    (result, url) = api.new_transation(request.args.get('amount', ''), str(uuid.uuid4()))

    return render_template('start.html', result=result, url=url)


@app.route('/back')
def back():

    return render_template('back.html', result='ok' in request.args)


@app.route('/ipn', methods=['POST'])
def ipn():

    print api.check_ipn(request.form)

    return ''

if __name__ == "__main__":
    app.run(debug=True)
