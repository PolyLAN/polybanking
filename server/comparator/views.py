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

from django.utils.timezone import now
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import csv

from comparator.forms import CompareForm

from configs.models import Config
from paiements.models import Transaction


def find_columns(csvreader):
    """Find columns ID in the CSV"""

    found_header = False

    postfinance_id_col = None
    our_id_col = None
    status_col = None
    montant_col = None

    for row in csvreader:
        if row[0][0] != '<':  # Postfinance love <xml>

            try:
                postfinance_id_col = row.index('Id')
                our_id_col = row.index('REF')
                status_col = row.index('STATUS')
                montant_col = row.index('TOTAL')

                found_header = True
            except ValueError:
                pass

            break

    return (found_header, postfinance_id_col, our_id_col, status_col, montant_col)


def find_dates(csvreader):
    """Find start and end date"""

    found_header = False
    start_date = None
    end_date = None

    for row in csvreader:
        if row[0][0] != '<':  # Postfinance love <xml>

            if not found_header:
                try:
                    date_col = row.index('ORDER')
                    found_header = True
                except ValueError:
                    pass
            else:

                date = parse(row[date_col], dayfirst=True)

                if start_date is None or start_date > date:
                    start_date = date

                if end_date is None or end_date < date:
                    end_date = date

    return (start_date, end_date)


def get_transactions(csvreader, postfinance_id_col, our_id_col, status_col, montant_col):
    """Return the list of transaction from the CSV"""

    retour = {}
    found_header = False

    for row in csvreader:
        if row[0][0] != '<':  # Postfinance love <xml>

            if not found_header:
                found_header = True
            else:

                try:
                    transaction = {}
                    transaction['postfinance_id'] = row[postfinance_id_col]
                    transaction['internal_id'] = row[our_id_col]
                    transaction['status'] = row[status_col]
                    transaction['montant'] = int(float(row[montant_col].replace(',', '.')) * 100)
                    transaction['montant_chf'] = float(row[montant_col].replace(',', '.'))

                    retour[row[our_id_col]] = transaction
                except ValueError:
                    pass

    return retour


@login_required
@user_passes_test(lambda u: u.is_superuser)
def home(request):
    """Show the form to export data"""

    if request.method == 'POST':  # If the form has been submitted...
        form = CompareForm(request.POST, request.FILES)

        if form.is_valid():  # If the form is valid

            def build_reader():
                return csv.reader(request.FILES['file'], delimiter=';', quotechar='|')

            result = ''
            transactions_ok = []
            transactions_diff = []
            transactions_only_csv = []
            transactions_only_local = []

            (found_header, postfinance_id_col, our_id_col, status_col, montant_col) = find_columns(build_reader())

            if not found_header:
                result = 'error_header'
            else:
                request.FILES['file'].seek(0)

                (start_date, end_date) = find_dates(build_reader())

                if not start_date or not end_date:
                    result = 'error_dates'
                else:

                    transactions_csv = get_transactions(build_reader(), postfinance_id_col, our_id_col, status_col, montant_col)

                    if not transactions_csv:
                        result = 'error_no_transaction'
                    else:

                        for transaction in Transaction.objects.filter(config__test_mode=form.cleaned_data['compare_test_configs']).filter(creation_date__gte=start_date, creation_date__lt=end_date + relativedelta(days=+1, seconds=-1)).all():

                            pid = 'polybanking-' + str(transaction.pk)

                            if pid not in transactions_csv:
                                transactions_only_local.append(transaction)
                            else:

                                transaction_csv = transactions_csv[pid]

                                if transaction_csv['postfinance_id'] == transaction.postfinance_id and transaction_csv['montant'] == transaction.amount and transaction_csv['status'] == transaction.postfinance_status:
                                    transactions_ok.append(transaction)
                                else:
                                    transactions_diff.append((transaction, transaction_csv))

                                del transactions_csv[pid]

                        for tId in transactions_csv:
                            transactions_only_csv.append(transactions_csv[tId])

            return render_to_response('comparator/result.html', {'result': result, 'transactions_ok': transactions_ok, 'transactions_diff': transactions_diff, 'transactions_only_csv': transactions_only_csv, 'transactions_only_local': transactions_only_local}, context_instance=RequestContext(request))

    else:
        form = CompareForm()

    return render_to_response('comparator/home.html', {'form': form}, context_instance=RequestContext(request))
