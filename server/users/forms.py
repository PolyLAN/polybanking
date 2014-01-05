from django.forms import ModelForm

from django.contrib.auth.models import User


class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ('password', 'last_login', 'date_joined', 'groups', 'user_permissions')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields["is_superuser"].help_text = 'Check to give admin rights to this user'
        self.fields["is_staff"].help_text = 'Check to give this user the right to create configs'
