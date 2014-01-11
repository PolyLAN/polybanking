from celery import task

import requests
from paiements.models import Transaction, TransactionLog

from django.utils.timezone import now

from libs.utils import compute_sign


@task(ignore_result=True)
def send_ipn(transactionPk):
    """Send IPN about a transaction"""

    transaction = Transaction.objects.get(pk=transactionPk)

    if not transaction.config.active or not transaction.config.admin_enable:
        return

    data = {'config': str(transaction.config.pk), 'reference': transaction.reference, 'postfinance_status': transaction.postfinance_status, 'postfinance_status_good': str(transaction.postfinance_status_good()), 'last_update': str(transaction.last_postfinance_ipn_date)}
    data['sign'] = compute_sign(transaction.config.key_ipn, data)

    try:
        error = requests.post(transaction.config.url_ipn, data=data).status_code != 200
    except:
        error = True

    if not error:
        transaction.last_ipn_date = now()
        transaction.ipn_needed = False
        transaction.save(update_fields=['last_ipn_date', 'ipn_needed'])

        TransactionLog(transaction=transaction, log_type='ipnsuccess', extra_data='').save()
    else:
        TransactionLog(transaction=transaction, log_type='ipnfailled', extra_data='').save()
