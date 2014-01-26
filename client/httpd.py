"""This example show a full http server.
"""
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

    (result, url) = api.new_transaction(request.args.get('amount', ''), str(uuid.uuid4()))

    return render_template('start.html', result=result, url=url)


@app.route('/back')
def back():

    transaction_list = api.get_transactions(max_transaction=3)

    transaction_details = api.get_transaction(transaction_list[0]['reference'])
    transaction_logs = api.get_transaction_logs(transaction_list[0]['reference'])

    return render_template('back.html', result='ok' in request.args, last_transactions=transaction_list, last_transaction_detail=transaction_details, last_transaction_logs=transaction_logs)


@app.route('/ipn', methods=['POST'])
def ipn():

    print api.check_ipn(request.form)

    return ''

if __name__ == "__main__":
    app.run(debug=False)
