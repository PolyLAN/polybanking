import hashlib


def compute_sign(secret, data):
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
