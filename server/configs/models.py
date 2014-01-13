from django.db import models
from django.contrib.auth.models import User
from django.utils.html import escape

import uuid
import datetime
import random
import hashlib


class Config(models.Model):
    """Represent a website configuration"""

    name = models.CharField(max_length=255)

    active = models.BooleanField(default=True)
    admin_enable = models.BooleanField(default=True)

    test_mode = models.BooleanField(default=True)

    url_ipn = models.URLField()
    url_back_ok = models.URLField()
    url_back_err = models.URLField()

    key_request = models.CharField(max_length=255)
    key_ipn = models.CharField(max_length=255)
    key_api = models.CharField(max_length=255)

    allowed_users = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        bonus = u''

        if self.test_mode:
            bonus += u'<i class="fa fa-flask"></i>'

        if not self.active or not self.admin_enable:
            bonus += u'<i class="glyphicon glyphicon-ban-circle"></i>'

        if bonus:
            bonus = u' (' + bonus + u')'

        return escape(self.name) + bonus

    def build_user_list(self):
        """Return a list of user in text format"""
        return u','.join([user.username for user in self.allowed_users.order_by('username')])

    def generate_diff(self, other):
        """Generate diff from this objet an another one (for logs)"""
        retour = u'\n\n'

        for (prop, prop_name) in (('name', 'Name'), ('active', 'Active'), ('admin_enable', 'Admin enable'), ('test_mode', 'Test mode'), ('url_ipn', 'URL Ipn'), ('url_back_ok', 'Return URL for success'), ('url_back_err', 'Return URL for error')):
            if not other.pk or getattr(self, prop) != getattr(other, prop):
                retour += unicode(prop_name) + u'=' + unicode(getattr(self, prop))

                if other.pk:
                    retour += u' (was ' + unicode(getattr(other, prop)) + u')'

                retour += u'\n'

        retour += u'User list: ' + self.build_user_list()
        return retour

    def is_user_allowed(self, user):
        """Return true is a user is allowed to display / edit the config"""

        if user.is_superuser:
            return True
        elif not self.pk:
            return user.is_staff  # Only staff can create configs
        else:
            return user in self.allowed_users

    def gen_key(self):
        """Return a random key suitable for keys of the model"""

        h = hashlib.sha512()

        for i in range(0, 2):
            h.update(str(uuid.uuid4()))
            h.update(str(datetime.datetime.now()))
            h.update(str(random.random()))
            h.update(str(self.pk))
            h.update(self.name)

        return h.hexdigest()

    def gen_key_api(self):
        """Generate a new key for api"""
        self.key_api = self.gen_key()

    def gen_key_ipn(self):
        """Generate a new key for ipn"""
        self.key_ipn = self.gen_key()

    def gen_key_request(self):
        """Generate a new key for requests"""
        self.key_request = self.gen_key()

    def save(self, *args, **kwargs):
        """Overide the save request to check if all keys have been generated"""

        if not self.key_api:
            self.gen_key_api()

        if not self.key_ipn:
            self.gen_key_ipn()

        if not self.key_request:
            self.gen_key_request()

        super(Config, self).save(*args, **kwargs)


class ConfigLogs(models.Model):

    config = models.ForeignKey(Config)
    user = models.ForeignKey(User)
    when = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
