from django import forms
from django.utils.translation import ugettext_lazy as _


from configs.models import Config


class ConfigModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name + (' (Test)' if obj.test_mode else '')


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
        ('custom', _('Custom')),
    ]

    all_config = forms.BooleanField(help_text=_('Export transactions from all configs'), required=False)
    config = ConfigModelChoiceField(queryset=None, required=False)

    file_type = forms.ChoiceField(choices=FILE_TYPE_CHOICES)

    range = forms.ChoiceField(choices=RANGE_CHOICES)

    custom_start = forms.DateTimeField(required=False)
    custom_end = forms.DateTimeField(required=False)

    def __init__(self, user, *args, **kwargs):
        super(ExportForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            del self.fields['all_config']
            self.fields['config'].queryset = Config.objects.filter(allowed_users=user).order_by('name').all()
        else:
            self.fields['config'].queryset = Config.objects.order_by('name').all()

    def clean(self):
        cleaned_data = super(ExportForm, self).clean()

        all_config = cleaned_data.get('all_config', False)
        config = cleaned_data.get('config', None)

        if not all_config and not config:
            raise forms.ValidationError(_('Please select a config'))

        range = cleaned_data.get('range')
        custom_start = cleaned_data.get('custom_start')
        custom_end = cleaned_data.get('custom_end')

        if range == 'custom' and (not custom_start or not custom_end):
            raise forms.ValidationError(_('Please select start and end date'))

        return cleaned_data


class SummaryForm(forms.Form):

    RANGE_CHOICES = [
        ('thismonth', _('This month')),
        ('previousmonth', _('The previous month')),
        ('sincemonth', _('Since a month')),
        ('thisyear', _('This year')),
        ('sinceyear', _('Since a year')),
        ('custom', _('Custom')),
    ]

    TRANSACTION_LIST = [
        ('no', _('No')),
        ('grouped', _('Grouped')),
        ('list', _('Yes'))
    ]

    include_test = forms.BooleanField(help_text=_('Export transactions from all config'), required=False)

    transactions = forms.ChoiceField(choices=TRANSACTION_LIST, help_text=_('Include transactions?'))

    range = forms.ChoiceField(choices=RANGE_CHOICES)

    custom_start = forms.DateTimeField(required=False)
    custom_end = forms.DateTimeField(required=False)

    def clean(self):
        cleaned_data = super(SummaryForm, self).clean()

        range = cleaned_data.get('range')
        custom_start = cleaned_data.get('custom_start')
        custom_end = cleaned_data.get('custom_end')

        if range == 'custom' and (not custom_start or not custom_end):
            raise forms.ValidationError(_('Please select start and end date'))

        return cleaned_data
