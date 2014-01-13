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
import uuid
from libs.postfinance import buildPostFinance

from configs.models import Config
from paiements.models import Transaction, TransactionLog
from paiements.tasks import send_ipn
from libs import utils

from django.utils.timezone import now


def build_error(status, error_code=400):
    """Build an error response"""
    return HttpResponse(json.dumps({'status': status, 'url': ''}), status=error_code)


@csrf_exempt
def start(request):
    """Start a new request"""

    if request.method != 'POST':
        build_error('BAD_REQUEST_TYPE', error_code=405)

    return build_error('CONFIG_ERROR', )
    # Get config
    try:
        config = Config.objects.get(pk=request.POST.get('config_id'), active=True, admin_enable=True)
    except:
        return build_error('CONFIG_ERROR', )

    # Check signature
    data = {}

    for key in ('amount', 'reference', 'extra_data', 'config_id'):
        data[key] = request.POST.get(key, '')

    if utils.compute_sign(config.key_request, data) != request.POST.get('sign'):
        return build_error('KEY_ERROR')

    # Check if amount > 0
    try:
        amount = int(request.POST.get('amount'))
    except ValueError:
        return build_error('AMOUNT_ERROR')

    if amount <= 0:
        return build_error('AMOUNT_ERROR')

    # Check if reference is unique
    reference = request.POST.get('reference')

    if config.transaction_set.filter(reference=reference).exists():
        return build_error('REFERENCE_ERROR')

    # Create transaction
    extra_data = request.POST.get('extraData', '')

    t = Transaction(config=config, reference=reference, extra_data=extra_data, amount=amount)
    t.save()

    # Log it
    TransactionLog(transaction=t, log_type='created').save()

    return HttpResponse(json.dumps({'status': 'OK', 'url': settings.EXTERNAL_BASE_URL + reverse('paiements.views.go', args=(t.pk,))}))


def go(request, pk):
    """Redirect the user to the postfinance website"""

    # Get transaction
    t = get_object_or_404(Transaction, pk=pk, config__active=True, config__admin_enable=True)

    if t.internal_status == 'fb':
        raise Http404

    postFinance = buildPostFinance(t.config.test_mode)

    fields = {
        'AMOUNT': str(t.amount),
        'ORDERID': 'polybanking-' + str(t.pk),
        'PSPID': postFinance.getPspIp(),
        'CURRENCY': 'CHF',
        }

    fields['SHASIGN'] = postFinance.computeInSign(fields)

    if t.config.test_mode:
        urlDest = settings.POSTFINANCE_TEST_URL
    else:
        urlDest = settings.POSTFINANCE_PROD_URL

    TransactionLog(transaction=t, log_type='userForwarded', extra_data=request.META['REMOTE_ADDR']).save()

    t.internal_status = 'fw'
    t.last_userforwarded_date = now()
    t.save(update_fields=['internal_status', 'last_userforwarded_date'])

    return render_to_response('paiements/go.html', {'fields': fields, 'urlDest': urlDest}, context_instance=RequestContext(request))


@csrf_exempt
def ipn(request):
    """Call by Postfinance website about status"""

    # Get transaction pk
    orderId = request.POST.get('orderID', '')

    if '-' in orderId:
        (who, pk) = orderId.split('-', 2)
    else:
        #should also raise an error
        build_error('UNVALID_ ID')

    if who != 'polybanking':
        raise Http404

    # Get transaction
    t = get_object_or_404(Transaction, pk=pk, config__active=True, config__admin_enable=True)

    if t.internal_status == 'cr':
        raise Http404

    postFinance = buildPostFinance(t.config.test_mode)

    # Check sign
    args = {}

    for a in request.POST:
        if a != 'SHASIGN':
            val = request.POST.get(a)
            if val:
                args[a.upper()] = val

    if request.POST.get('SHASIGN').upper() != postFinance.computeOutSign(args).upper():
        raise Http404

    # Let's catch the ID
    if not t.postfinance_id:
        t.postfinance_id = request.POST.get('PAYID')
        TransactionLog(transaction=t, log_type='postfinanceId', extra_data=request.META['REMOTE_ADDR']).save()

    t.internal_status = 'fb'
    t.last_postfinance_ipn_date = now()
    t.postfinance_status = request.POST.get('STATUS')
    t.ipn_needed = True
    t.save(update_fields=['internal_status', 'last_postfinance_ipn_date', 'postfinance_status', 'ipn_needed', 'postfinance_id'])

    TransactionLog(transaction=t, log_type='postfinanceStatus', extra_data=request.POST.get('STATUS')).save()

    send_ipn.delay(t.pk)

    return HttpResponse('')


@csrf_exempt
def return_from_postfinance(request):
    """Client is returnting from postfinance"""

    # Get transaction pk
    orderId = request.GET.get('orderID')

    (who, pk) = orderId.split('-', 2)

    if who != 'polybanking':
        raise Http404

    # Get transaction
    t = get_object_or_404(Transaction, pk=pk, config__active=True, config__admin_enable=True)

    if t.internal_status == 'cr':
        raise Http404

    postFinance = buildPostFinance(t.config.test_mode)

    # Check sign
    args = {}

    for a in request.GET:
        if a != 'SHASIGN':
            args[a.upper()] = request.GET.get(a)

    if request.GET.get('SHASIGN').upper() != postFinance.computeOutSign(args).upper():
        raise Http404

    # Let's catch the ID
    if not t.postfinance_id:
        t.postfinance_id = request.GET.get('PAYID')
        TransactionLog(transaction=t, log_type='postfinanceId', extra_data=request.META['REMOTE_ADDR']).save()

    t.internal_status = 'fb'
    t.last_user_back_from_postfinance_date = now()
    t.save(update_fields=['internal_status', 'last_user_back_from_postfinance_date', 'postfinance_id'])

    TransactionLog(transaction=t, log_type='userBackFromPostfinance', extra_data=request.META['REMOTE_ADDR']).save()

    #  9 or 5 are good signs
    if request.GET.get('STATUS') in ['9', '5']:
        return HttpResponseRedirect(t.config.url_back_ok)
    else:
        return HttpResponseRedirect(t.config.url_back_err)


@login_required
def transactions_list(request):
    """Show the transactions list"""

    configPk = request.GET.get('configPk', 'NothingSelected')

    if request.user.is_superuser:
        available_configs = Config.objects
    else:
        available_configs = Config.objects.filter(allowed_users=request.user)

    available_configs = available_configs.order_by('name').all()

    if configPk == 'NothingSelected':
        if request.user.is_superuser:
            configPk = 'all'
        elif len(available_configs) > 0:
            configPk = available_configs[0]

    if configPk != 'all' or not request.user.is_superuser:
        try:
            config = get_object_or_404(Config, pk=configPk)
        except:
            config = None

        transactions = Transaction.objects.filter(config=config)
    else:
        transactions = Transaction.objects
        config = None

    transactions = transactions.order_by('-creation_date').all()

    return render_to_response('paiements/transactions/list.html', {'list': transactions, 'available_configs': available_configs, 'configPk': configPk, 'config': config}, context_instance=RequestContext(request))


@login_required
def transactions_show_logs(request, pk):
    """Show logs of transactions"""

    object = get_object_or_404(Transaction, pk=pk)

    if not request.user.is_superuser and not request.user in object.allowed_users:
        raise Http404

    list = object.transactionlog_set.order_by('-when').all()

    return render_to_response('paiements/transactions/logs.html', {'object': object, 'list': list}, context_instance=RequestContext(request))


@login_required
def transactions_show(request, pk):
    """Display details of a transaction"""

    object = get_object_or_404(Transaction, pk=pk)

    if not request.user.is_superuser and not request.user in object.allowed_users:
        raise Http404

    return render_to_response('paiements/transactions/show.html', {'object': object}, context_instance=RequestContext(request))


@login_required
def transactions_send_ipn(request, pk):

    object = get_object_or_404(Transaction, pk=pk)

    if not request.user.is_superuser and not request.user in object.allowed_users:
        raise Http404

    send_ipn.delay(object.pk)

    messages.success(request, _('IPN has been queued !'))

    return redirect('paiements.views.transactions_show', object.pk)
