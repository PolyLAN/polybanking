# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators import require_GET
from django.utils.translation import ugettext_lazy as _


import json


from configs.models import Config
from paiements.models import Transaction


@csrf_exempt
@require_GET
def transactions_list(request):
    """Return the list of transaction"""
    config_pk = request.GET.get('config_id', -1)
    secret = request.GET.get('secret', '#')

    config = get_object_or_404(Config, pk=config_pk, key_api=secret)
    try:
        max_transaction = int(request.GET['max_transaction'])
    except (ValueError, KeyError):
        max_transaction = 100

    retour = []

    for transaction in config.transaction_set.order_by('-creation_date')[:max_transaction]:
        retour.append({'reference': transaction.reference})

    return HttpResponse(json.dumps({'result': 'ok', 'data': retour}))


@csrf_exempt
@require_GET
def transactions_show(request, reference):
    """Return details of a transaction"""
    config_pk = request.GET.get('config_id', -1)
    secret = request.GET.get('secret', '#')

    config = get_object_or_404(Config, pk=config_pk, key_api=secret)

    transaction = get_object_or_404(Transaction, config=config, reference=reference)

    return HttpResponse(json.dumps({'result': 'ok', 'data': transaction.dump_api()}))


@csrf_exempt
@require_GET
def transactions_show_logs(request, reference):
    """Return logs of a transaction"""
    config_pk = request.GET.get('config_id', -1)
    secret = request.GET.get('secret', '#')

    config = get_object_or_404(Config, pk=config_pk, key_api=secret)

    transaction = get_object_or_404(Transaction, config=config, reference=reference)

    retour = []

    for log in transaction.transactionlog_set.order_by('-when'):
        retour.append(log.dump_api())

    return HttpResponse(json.dumps({'result': 'ok', 'data': retour}))
