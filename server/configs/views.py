# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.db import connections
from django.core.paginator import InvalidPage, EmptyPage, Paginator
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from configs.models import Config, ConfigLogs
from configs.forms import ConfigForm
from django.contrib.auth.models import User


@login_required
def list(request):
    """Show the list of configs"""

    if request.user.is_superuser:
        list = Config.objects.order_by('name').all()
    else:
        list = Config.objects.filter(allowed_users=request.user).order_by('name').all()

    return render_to_response('configs/configs/list.html', {'list': list}, context_instance=RequestContext(request))


@login_required
def edit(request, pk):
    """Edit or create a config"""

    try:
        config = Config.configs.get(pk=pk)
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
                ConfigLogs(config=config, user=request.user, text=_('Config has been updated: ') + config.generate_diff(Config.configs.get(pk=pk))).save()

            config.save()  # To use allowed_users

            config.allowed_users.clear()

            for u in request.POST.get('allowed_users', []):
                config.allowed_users.add(User.configs.get(pk=u))
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
def show(request, pk):
    """Show a config"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    return render_to_response('configs/configs/show.html', {'object': object}, context_instance=RequestContext(request))


@login_required
def new_ipn_key(request, pk):
    """Generate a new ipn key"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    object.gen_key_ipn()
    object.save()

    ConfigLogs(config=object, user=request.user, text=_('A new IPN key has been generated.')).save()

    messages.success(request, _('A new IPN key has been generated !'))

    return redirect('configs.views.show', pk=pk)


@login_required
def new_requests_key(request, pk):
    """Generate a new request key"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    object.gen_key_request()
    object.save()

    ConfigLogs(config=object, user=request.user, text=_('A new requests key has been generated.')).save()

    messages.success(request, _('A new requests key has been generated !'))

    return redirect('configs.views.show', pk=pk)


@login_required
def new_api_key(request, pk):
    """Generate a new api key"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    object.gen_key_api()
    object.save()

    ConfigLogs(config=object, user=request.user, text=_('A new api key has been generated.')).save()

    messages.success(request, _('A new api key has been generated !'))

    return redirect('configs.views.show', pk=pk)


@login_required
def show_logs(request, pk):
    """Display config's logs"""

    object = get_object_or_404(Config, pk=pk)

    if not object.is_user_allowed(request.user):
        raise Http404

    list = object.configlogs_set.order_by('-when').all()

    return render_to_response('configs/configs/logs.html', {'object': object, 'list': list}, context_instance=RequestContext(request))
