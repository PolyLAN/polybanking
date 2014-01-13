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


import json


from configs.models import Config
from paiements.models import Transaction, TransactionLog


@csrf_exempt
def transactions_list(request):
    """Return the list of transaction"""

    config = get_object_or_404(Config, pk=request.POST.get('config_id', -1), key_api=request.POST.get('secret', '#'))

    max_transaction = int(request.POST.get('max_transaction', '100'))

    retour = []

    for transaction in config.transaction_set.order_by('-creation_date').all()[:max_transaction]:
        retour.append({'reference': transaction.reference})

    return HttpResponse(json.dumps({'result': 'ok', 'data': retour}))


@csrf_exempt
def transactions_show(request, reference):
    """Return details of a transaction"""

    config = get_object_or_404(Config, pk=request.POST.get('config_id', -1), key_api=request.POST.get('secret', '#'))

    transaction = get_object_or_404(Transaction, config=config, reference=reference)

    return HttpResponse(json.dumps({'result': 'ok', 'data': transaction.dump_api()}))


@csrf_exempt
def transactions_show_logs(request, reference):
    """Return logs of a transaction"""

    config = get_object_or_404(Config, pk=request.POST.get('config_id', -1), key_api=request.POST.get('secret', '#'))

    transaction = get_object_or_404(Transaction, config=config, reference=reference)

    retour = []

    for log in transaction.transactionlog_set.order_by('-when').all():
        retour.append(log.dump_api())

    return HttpResponse(json.dumps({'result': 'ok', 'data': retour}))
