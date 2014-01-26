
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'polybanking',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'polybanking',
        'PASSWORD': '%(mysql_password)s',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}


# Make this unique, and don't share it with anybody.
SECRET_KEY = '%(secret_key)s'

SHA_IN_TEST = ''
SHA_OUT_TEST = ''

SHA_IN_PROD = ''
SHA_OUT_PROD = ''

EXTERNAL_BASE_URL = ''

POSTFINANCE_TEST_URL = 'https://e-payment.postfinance.ch/ncol/test/orderstandard.asp'
POSTFINANCE_PROD_URL = 'https://e-payment.postfinance.ch/ncol/prod/orderstandard.asp'

PSPID_TEST = ''
PSPID_PROD = ''

CURRENCY = 'CHF'

BROKER_URL = 'amqp://polybanking:%(rabbitmq_password)s@localhost:5672//'
