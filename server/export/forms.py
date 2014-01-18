from django import forms
from django.utils.translation import ugettext_lazy as _


from configs.models import Config


class ExportForm(forms.Form):

    FILE_TYPE_CHOICES = (
        ('json', _('JSON')),
        ('xml', _('XML')),
        ('csv', _('CSV (Without logs)')),
    )

    RANGE_CHOICES = [
        ('thismonth', _('This month')),
        ('previousmonth', _('The previous month')),
        ('sincemonth', _('Since a month')),
        ('thisyear', _('This year')),
        ('sinceyear', _('Since a year')),
    ]

    all_config = forms.BooleanField(help_text=_('Export transactions from all configs'), required=False)
    config = forms.ModelChoiceField(queryset=None)

    file_type = forms.ChoiceField(choices=FILE_TYPE_CHOICES)

    range = forms.ChoiceField(choices=RANGE_CHOICES)

    def __init__(self, user, *args, **kwargs):
        super(ExportForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            del self.fields['all_config']
            self.fields['config'].queryset = Config.objects.filter(allowed_users=user).order_by('name').all()
        else:
            self.fields['config'].queryset = Config.objects.order_by('name').all()


class SummaryForm(forms.Form):

    RANGE_CHOICES = [
        ('thismonth', _('This month')),
        ('previousmonth', _('The previous month')),
        ('sincemonth', _('Since a month')),
        ('thisyear', _('This year')),
        ('sinceyear', _('Since a year')),
    ]

    include_test = forms.BooleanField(help_text=_('Export transactions from all config'), required=False)

    range = forms.ChoiceField(choices=RANGE_CHOICES)
