# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.http import Http404
from django.views.decorators import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from configs.models import Config, ConfigLogs
from configs.forms import ConfigForm
from django.contrib.auth.models import User


@login_required
@require_GET
def list(request):
    """Show the list of configs"""

    if request.user.is_superuser:
        configs = Config.objects.order_by('name')
    else:
        configs = Config.objects.filter(allowed_users=request.user).order_by('name')

    return render_to_response('configs/configs/list.html', {'list': configs}, context_instance=RequestContext(request))


@login_required
def edit(request, pk):
    """Edit or create a config"""

    try:
        config = Config.objects.get(pk=pk)
        create = False
    except:
        config = Config()
        create = True

    if not config.is_user_allowed(request.user):
        raise Http404

    if request.method == 'POST':  # If the form has been submitted...
        form = ConfigForm(request.user, request.POST, instance=config)

        if form.is_valid():  # If the form is valid

            config = form.save(commit=False)

            if not create:
                ConfigLogs(config=config, user=request.user, text=_('Config has been updated: ') + config.generate_diff(Config.objects.get(pk=pk))).save()

            config.save()  # To use allowed_users

            config.allowed_users.clear()

            for u in request.POST.get('allowed_users', []):
                config.allowed_users.add(User.objects.get(pk=u))
            config.allowed_users.add(request.user)
            config.save()

            if create:
                ConfigLogs(config=config, user=request.user, text=_('Config has been created: ') + config.generate_diff(Config())).save()

            messages.success(request, _('The config has been saved.'))

            return redirect('configs.views.list')
    else:
        form = ConfigForm(request.user, instance=config)

    return render_to_response('configs/configs/edit.html', {'form': form}, context_instance=RequestContext(request))


# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def delete(request, pk):
#     """Delete a config"""

#     object = get_object_or_404(Config, pk=pk)

#     if not object.is_user_allowed(request.user):
#         raise Http404

#     object.delete()
#     messages.success(request, _('Config has been deleted.'))

#     return redirect('configs.views.list')


@login_required
@require_GET
def show(request, pk):
    """Show a config"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    return render_to_response('configs/configs/show.html', {'object': object}, context_instance=RequestContext(request))


@login_required
@require_GET
def new_key(request, pk, key_type):
    config = get_object_or_404(Config, pk=pk)

    if not config.is_user_allowed(request.user):
        raise Http404

    if key_type == "request":
        config.gen_key_request()
    elif key_type == "ipn":
        config.gen_key_ipn()
    elif key_type == "api":
        config.gen_key_api()
    config.save()
    
    log_message = _(u"A new {} key has been generated".format(key_type))
    ConfigLogs(config=config, user=request.user, text=log_message).save()

    messages.success(request, log_message)

    return redirect('configs.views.show', pk=pk)


@login_required
def show_logs(request, pk):
    """Display config's logs"""

    config = get_object_or_404(Config, pk=pk)

    if not config.is_user_allowed(request.user):
        raise Http404

    list = config.configlogs_set.order_by('-when')

    return render_to_response('configs/configs/logs.html', {'object': config, 'list': list}, context_instance=RequestContext(request))
