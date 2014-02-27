PolyBanking
===========

PolyBanking is a django application to be able to use PostFinance [E-payement](https://www.postfinance.ch/fr/biz/prod/eserv/epay.html?WT.ac=_techshortcut_bizprodeservepayfr)'s service with multiple website.

PolyBanking allow differents services, thought differents configuration to request payement. The system will ask and forward the user to Postfinance, and will report result and status of a payement back to website who created the request.

PolyBanking is able to compare PostFinance's reports with his database, export transactions and create differents reports from transations.

## License

PolyBanking is distributed with the [BSD](http://opensource.org/licenses/BSD-2-Clause) license. It includes code from Azimut-prod, Copyright (c) 2013 Azimut-Prod (Deployements scripts).

## Authors

PolyBanking has been developped by [Maximilien Cuony](https://github.com/the-glu) and reviwed by [Malik Bougacha](https://github.com/gcmalloc) for the [AGEPoly](http://agepoly.ch) and [PolyLAN](https://polylan.ch).

## Setup

### Fabric script

There is a fabric script usable to deploy the application on a *fresh* debian server. 

* Install fabric (`pip install fabric`)
* Clone the repository : `git clone git@github.com:PolyLAN/polybanking.git`
* Copy `Deployement/config.py.dist` to `Deployement/config.py`, edit values with random passswords.
* Run the fabric task: `cd Deployement` and `fab deploy_new`

You can upgrade the code using `fab update_code`

### Manualy

This is a 'normal' django project, you can deploy it as usual. There is a `app/settingsLocal.py.dist` file you have to copy to `app/settingsLocal.py` and edit values suiting your needs.

You can install python dependencies using `pip install -r data/pip-reqs.txt`.

The project use celery, so you will need a broker (like RabbitMq) and to run the celery deamon.

## Configuration

You have to edit the `app/settingsLocal.py` file (`/var/www/git-repo/polybanking/app/settingsLocal.py` if you used the fabric script) to set your Postfinance secrets (SHA_IN, SHA_OUT and PSPID) for production and test site.

### Authentification

By default, [Tequilla](https://tequila.epfl.ch/intro.html) is used. Edit `AUTHENTICATION_BACKENDS` in settings if you want to use something else.

## API & IPN

Clients communicate with PolyBanking using a Web API.

### Lib

A simple python lib is available, located in `client/libs/polybanking.py`.

Use `PolyBanking(server, config_id, keyRequests, keyIPN, keyAPI)` to create an new api object.

### Signs

Each requests parameters for new requests must be signed. IPN access from PolyBanking are also signed. There is 3 secrets, one to create new transations (`keyRequests`), one for IPN (`keyIPN`) and one for API access (`keyAPI`). The last one is not used for signatures !

Signatures are a SHA512 computed like this.

* Take parameters in order
* Take an empty string
* For each pair of parameter/value:
    * Replace ';' by '!!' and '=' by '??' in the parameter and the value
    * Concat to the base string '<parameter>=<value>;<secret>;'
* Compute the SHA512 of the string.

### New request

Create a new transaction.

* Base URL: /paiements/start/
* Api Call: new_transaction(amount, reference, extra_data='')
* POST parameters
    * `amount` : The amount, in CHF and in cents (Eg. for 5.50 CHF, set this to 550)
    * `reference` : An internal reference, who has to be unique
    * `extra_data` : Extra data. Can be anything.
    * `config_id` : The config to use
    * `sign` : Signature of parameters, using `keyRequests`secret.
    
* Return a JSON array:
    * `status`
        * `OK` : Success
        * `KEY_ERROR` : The sign is wrong
        * `CONFIG_ERROR` : The config is wrong
        * `AMOUNT_ERROR` : The amount is wrong
        * `REFERENCE_ERROR` : The reference is wrong or already usued.
        * `ERROR` : Generic error.
    * `url`
        * Where the client should be redirect to start the transaction

### Get transactions

Return a list of transaction for a config

* Base URL: /api/transactions/
* Api Call: get_transactions(max_transaction=100)
* POST parameters
    * `config_id` :  The config to use
    * `secret` : `keyAPI`
    * `max_transaction` : Maximum number of transactions to return
* Return a JSON array
    * `result`
        * `ok` : Success
    * `data` : The list of transaction, JSON encoded. Values are:
        * 'reference' : The reference

### Transaction details

Return details of a transction

* Base URL: /api/transactions/<reference>/
* Api Call: get_transaction(reference)
* POST parameters
    * `config_id` :  The config to use
    * `secret` : `keyAPI`
* Return a JSON array
    * `result`
        * `ok` : Success
    * `data` : The detail of transaction, JSON encoded. Values are:
        * 'reference' : The reference
        * 'extra_data' : The value of the extra_data filed when the transaction was created
        * 'amount' : Transaction's amount
        * 'postfinance_id' : The Postfinance ID
        * 'postfinance_status' : The Postfinance Status
        * 'internal_status' : The internal Status
        * 'ipn_needed' : True if IPN has to be send
        * 'creation_date' : The creation date of the transaction
        * 'last_userforwarded_date` : Last time the user was forwarded to Postfinance
        * 'last_user_back_from_postfinance_date' : Last time the user was back from Postfinance
        * 'last_postfinance_ipn_date' : Last time we got IPN data from postfinance
        * 'last_ipn_date' : Last time IPN data was send
        * 'postfinance_status_text' : The humain-readable postfinance status
        * 'internal_status_text' : The humain-readable status text

### Transaction logs

Return logs of a transction

* Base URL: /api/transactions/<reference>/logs/
* Api Call: transactions_show_logs(reference)
* POST parameters
    * `config_id` :  The config to use
    * `secret` : `keyAPI`
* Return a JSON array
    * `result`
        * `ok` : Success
    * `data` : The detail of transaction, JSON encoded. Values are:
        * `when` : Date of the entry
        * `extra_data` : Extra data for the entry, based on type
        * `log_type` : Type of the entry
        * `log_type_text` : Human-readable type of the entry.

### IPN

PolyBanking is able to send IPN notification to your server. Request is made using POST to the URL you set in the Config.

Post parameters are:

* `config` : The current config
* `reference` : The reference of the transction
* `postfinance_status` : The Postfinance status
* `postfinance_status_good` : True of the transaction status mean the payement was successfull.
* `last_update` : The date when the transaction as updated. You should check if you didn't recieved before a never transaction, to avoid reply attacts.

You can check if a post request is valid using the python lib with the `check_ipn(post_data)` function. The function return `(is_ok, message, reference, status, status_good, last_update)`, message can be 
* `SIGN` : Wrong signature
* `CONFIG` : Config id is wrong.

## Example client

An example client, using flask, is available in the `client/` folder. You can configure it using the `client/config.py`, a template is available: `client/config.py.dist`.

Use `python httpd.py` to run it, by default available at `http://127.0.0.1:5000`.