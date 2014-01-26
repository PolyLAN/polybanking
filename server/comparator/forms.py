from django import forms
from django.utils.translation import ugettext_lazy as _


class CompareForm(forms.Form):

    compare_test_configs = forms.BooleanField(help_text=_('Test mode'), required=False)

    file = forms.FileField(help_text=_('CSV export from Postfinance, defaults parameters'))
