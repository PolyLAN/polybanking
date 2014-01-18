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
from django.db.models import Sum
import cStringIO as StringIO
import ho.pisa as pisa
from django.template.loader import get_template
from django.template import Context
from cgi import escape

from export.forms import ExportForm, SummaryForm

from configs.models import Config
from paiements.models import Transaction


@login_required
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
                response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (file_name, )

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


@login_required
@user_passes_test(lambda u: u.is_superuser)
def summary(request):
    """Display a summary for configs, regrouped by groups"""

    if request.method == 'POST':  # If the form has been submitted...
        form = SummaryForm(request.POST)

        if form.is_valid():  # If the form is valid

            include_test = form.cleaned_data['include_test']
            range = form.cleaned_data['range']

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

            months = []

            # Let's build the list of perids, by month, to sum transaction
            current_date = start_date + relativedelta(minute=0, hour=0, second=0, microsecond=0)

            # While we don't have all dates
            while current_date < end_date:

                # The end is the current date, + one month, minus one second, with the day forced to one
                tmp_end_Date = current_date + relativedelta(months=+1, seconds=-1, day=1)

                # The next current date is +one month, at the start of the month
                next_current = current_date + relativedelta(months=+1, day=1)

                # If we are going to far, stoè
                if tmp_end_Date > end_date:
                    tmp_end_Date = end_date

                months.append((current_date, tmp_end_Date))

                current_date = next_current

            #transactions = transactions.filter(creation_date__gte=start_date, creation_date__lt=end_date).all()

            data = {}

            base_config_filter = Config.objects.filter(admin_enable=True).exclude(group=None)

            if not include_test:
                base_config_filter = base_config_filter.exclude(test_mode=True)

            for group in base_config_filter.order_by('group').values('group').distinct():

                groupName = group['group']

                data_group = []

                group_total = 0

                for config in base_config_filter.filter(group=groupName).all():

                    data_config = []
                    total = 0

                    for (sub_start_date, sub_end_date) in months:
                        query_sum = config.transaction_set.filter(postfinance_status='9', creation_date__gte=sub_start_date, creation_date__lt=sub_end_date).all().aggregate(Sum('amount'))

                        current_sum = query_sum['amount__sum']

                        if not current_sum:
                            current_sum = '0'

                        total_month = int(current_sum)

                        data_config.append((sub_start_date, sub_end_date, float(total_month) / 100.0, config))

                        total += total_month  # Sum in and not floats !

                    data_config.append(float(total) / 100.0)

                    data_group.append(data_config)

                    group_total += total

                data[groupName] = (data_group, float(group_total) / 100.0)

            template = get_template('export/summary_pdf.html')
            context = Context({'data': data, 'months': months, 'start_date': start_date, 'end_date': end_date})
            html = template.render(context)
            result = StringIO.StringIO()

            pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), result)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), mimetype='application/pdf')
                file_name = 'Summary_' + start_date.strftime('%Y-%m-%d_%H.%M.%S') + u' - ' + end_date.strftime('%Y-%m-%d_%H.%M.%S')
                response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % (file_name, )
                return response

            return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))

    else:
        form = SummaryForm()

    return render_to_response('export/summary.html', {'form': form}, context_instance=RequestContext(request))
