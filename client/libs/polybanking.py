import requests
import hashlib


class PolyBanking():
    """Api for polybanking accesses"""

    def __init__(self, server, config_id, keyRequests, keyIPN, keyAPI):
        self.server = server
        self.config_id = config_id
        self.keyRequests = keyRequests
        self.keyIPN = keyIPN
        self.keyAPI = keyAPI

    def compute_sign(self, secret, data):
        """Compute the signature for a dict"""

        def escape_chars(s):
            """Remove = and ; from a string"""
            return s.replace(';', '!!').replace('=', '??')

        h = hashlib.sha512()

        for key, value in sorted(data.iteritems(), key=lambda (k, v): k):
            h.update(escape_chars(key))
            h.update('=')
            h.update(escape_chars(value))
            h.update(';')
            h.update(secret)
            h.update(';')

        return h.hexdigest()

    def new_transation(self, amount, reference, extra_data=''):
        """Start a new transation, with the specified amount and reference. The reference must be unique.
        Return (Status, the URL where the user should be redirected or None)
        Status can be 'OK', 'KEY_ERROR', 'CONFIG_ERROR', 'AMOUNT_ERROR', 'REFERENCE_ERROR', 'ERROR'"""

        data = {'amount': amount, 'reference': reference, 'extra_data': extra_data, 'config_id': self.config_id}

        data['sign'] = self.compute_sign(self.keyRequests, data)

        try:
            result = requests.post(self.server + '/paiements/start/', data=data).json()
            return (result['status'], result['url'])
        except:
            return ('ERROR', '')
