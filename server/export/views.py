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
import json
import csv
from huTools.structured import dict2xml


from export.forms import ExportForm

from paiements.models import Transaction


def home(request):
    """Show the form to export data"""

    if request.method == 'POST':  # If the form has been submitted...
        form = ExportForm(request.user, request.POST)

        if form.is_valid():  # If the form is valid

            config = form.cleaned_data['config']
            all_config = form.cleaned_data['all_config']
            range = form.cleaned_data['range']
            file_type = form.cleaned_data['file_type']

            if not request.user.is_superuser and all_config:
                raise Http404

            if not request.user.is_superuser and not request.user in config.allowed_users:
                raise Http404

            transactions = Transaction.objects.order_by('creation_date')

            file_name = u'Export_'

            if not all_config:
                transactions = transactions.filter(config=config)

                file_name += transactions.name + u'_'

            else:

                file_name += u'ALL_'


            if range == 'thismonth':
                start_date = now() + relativedelta(day=1, minute=0, hour=0, second=0, microsecond=0)
                end_date = now() + relativedelta(day=1, months=+1, seconds=-1, minute=0, hour=0, second=0, microsecond=0)
            elif range == 'previousmonth':
                start_date = now() + relativedelta(day=1, months=-1, minute=0, hour=0, second=0, microsecond=0)
                end_date = now() + relativedelta(day=1, seconds=-1, minute=0, hour=0, second=0, microsecond=0)
            elif range == 'sincemonth':
                start_date = now() + relativedelta(months=-1)
                end_date = now()
            elif range == 'thisyear':
                start_date = now() + relativedelta(day=1, month=1, minute=0, hour=0, second=0, microsecond=0)
                end_date = now() + relativedelta(day=1, month=1, years=+1, seconds=-1, minute=0, hour=0, second=0, microsecond=0)
            elif range == 'sinceyear':
                start_date = now() + relativedelta(years=-1)
                end_date = now()

            transactions = transactions.filter(creation_date__gte=start_date, creation_date__lt=end_date).all()

            file_name += start_date.strftime('%Y-%m-%d_%H.%M.%S') + u' - ' + end_date.strftime('%Y-%m-%d_%H.%M.%S')


            # Commong for json and xml
            data = [dict(tr.dump_api().items() + {'logs': [log.dump_api() for log in tr.transactionlog_set.order_by('when').all()]}.items()) for tr in transactions]

            if file_type == 'json':

                response = HttpResponse(json.dumps(data), content_type='text/json')

                response['Content-Disposition'] = 'attachment; filename="%s.json"' % (file_name, )

                return response

            elif file_type == 'xml':


                response = HttpResponse(dict2xml({'export': data}, pretty=True), content_type='text/xml')

                response['Content-Disposition'] = 'attachment; filename="%s.xml"' % (file_name, )

                return response

            elif file_type == 'csv':

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="%s.csv"'  % (file_name, )

                writer = csv.writer(response)

                headers = ['reference', 'extra_data', 'amount', 'postfinance_id', 'postfinance_status', 'internal_status', 'ipn_needed', 'creation_date', 'last_userforwarded_date', 'last_user_back_from_postfinance_date', 'last_postfinance_ipn_date', 'last_ipn_date', 'postfinance_status_text', 'internal_status_text']

                writer.writerow(headers)

                for tr in transactions:
                    data = []
                    trdata = tr.dump_api()

                    for val in headers:
                        data.append(trdata[val])

                    writer.writerow(data)

                return response



    else:
        form = ExportForm(request.user)

    return render_to_response('export/home.html', {'form': form}, context_instance=RequestContext(request))
