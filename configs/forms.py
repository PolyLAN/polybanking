from django.forms import ModelForm

from configs.models import Config


class ConfigForm(ModelForm):
    class Meta:
        model = Config
        exclude = ('key_request', 'key_ipn', 'key_api')

    def __init__(self, user, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            del self.fields['admin_enable']

        if kwargs['instance'].pk:
            del self.fields['test_mode']
