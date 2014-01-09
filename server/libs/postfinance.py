import requests
import hashlib
from django.conf import settings


class PostFinance():
    """Api for postfinance"""

    def __init__(self, SHA_IN, SHA_OUT, PSPID, testMode=False):
        self.SHA_IN = SHA_IN
        self.SHA_OUT = SHA_OUT
        self.PSPID = PSPID
        self.testMode = testMode

    def computeSign(self, secret, data):
        """Compute a SHA signature following PostFinance's protocol"""

        h = hashlib.sha512()

        for key, value in sorted(data.iteritems(), key=lambda (k, v): k):
            h.update(key)
            h.update('=')
            h.update(value)
            h.update(secret)

        return h.hexdigest()

    def computeOutSign(self, data):
        """Compute a SHA signature following PostFinance's protocol using OUT key"""
        return self.computeSign(self.SHA_OUT, data)

    def computeInSign(self, data):
        """Compute a SHA signature following PostFinance's protocol using IN key"""
        return self.computeSign(self.SHA_IN, data)

    def getPspIp(self):
        """Return the pspId"""
        return self.PSPID


def buildPostFinance(testMode=False):
    """Return a postfinance object with correct parameters"""

    if testMode:
        return PostFinance(settings.SHA_IN_TEST, settings.SHA_OUT_TEST, settings.PSPID_TEST, True)
    else:
        return PostFinance(settings.SHA_IN_PROD, settings.SHA_OUT_PROD, settings.PSPID_PROD, False)
