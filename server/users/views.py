# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
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

from django.contrib.auth.models import User
from users.forms import UserForm


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list(request):
    """Show the list of users"""

    list = User.objects.order_by('first_name').all()

    return render(request, 'users/users/list.html', {'list': list})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit(request, pk):
    """Edit or create an user"""

    try:
        object = User.objects.get(pk=pk)
    except:
        object = User()

    if request.method == 'POST':  # If the form has been submitted...
        form = UserForm(request.POST, instance=object)

        if form.is_valid():  # If the form is valid
            object = form.save()

            messages.success(request, _('The user has been saved.'))

            return redirect('users.views.list')
    else:
        form = UserForm(instance=object)

    return render(request, 'users/users/edit.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete(request, pk):
    """Delete an user"""

    object = get_object_or_404(User, pk=pk)

    # Don't delete ourself
    if object.pk != request.user.pk:
        object.delete()
        messages.success(request, _('User has been deleted.'))
    else:
        messages.warning(request, _('You cannot delete yourself !'))

    return redirect('users.views.list')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def show(request, pk):
    """Display an user"""

    object = get_object_or_404(User, pk=pk)

    return render(request, 'users/users/show.html', {'object': object})
