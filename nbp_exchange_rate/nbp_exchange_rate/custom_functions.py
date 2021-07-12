# imports from utils.py
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, add_days
from frappe.utils import get_datetime_str, nowdate
from erpnext import get_default_company

# custom imports
import requests
import datetime

# ------ function from ERPNext code with modification ------------
# TODO in future: keep up to date with erpnext/setup/utils.py

@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, transaction_date=None, args=None):
	if not (from_currency and to_currency):
		# manqala 19/09/2016: Should this be an empty return or should it throw and exception?
		return
	if from_currency == to_currency:
		return 1

	if not transaction_date:
		transaction_date = nowdate()
	currency_settings = frappe.get_doc("Accounts Settings").as_dict()
	allow_stale_rates = currency_settings.get("allow_stale")

	filters = [
		["date", "<=", get_datetime_str(transaction_date)],
		["from_currency", "=", from_currency],
		["to_currency", "=", to_currency]
	]

	if args == "for_buying":
		filters.append(["for_buying", "=", "1"])
	elif args == "for_selling":
		filters.append(["for_selling", "=", "1"])

	if not allow_stale_rates:
		stale_days = currency_settings.get("stale_days")
		checkpoint_date = add_days(transaction_date, -stale_days)
		filters.append(["date", ">", get_datetime_str(checkpoint_date)])

	# cksgb 19/09/2016: get last entry in Currency Exchange with from_currency and to_currency.
	entries = frappe.get_all(
		"Currency Exchange", fields=["exchange_rate"], filters=filters, order_by="date desc",
		limit=1)
	if entries:
		return flt(entries[0].exchange_rate)

	try:
		cache = frappe.cache()

		# ------------ customized key ----------------
		if args == None:
			args = "both"
		key = "nbp_exchange_rate_{0}:{1}:{2}:{3}".format(transaction_date,from_currency, to_currency, args)

		value = cache.get(key)

		if not value:
			# --------- custom code -------------

			if to_currency != "PLN":
				raise Exception(_("NBP exchange rates are available in PLN only."))

			if args == "for_buying":
				value = get_nbp_exchange_rate(transaction_date, from_currency, table_code = 'a', rate_type = 'mid')
			elif args == "for_selling":
				value = get_nbp_exchange_rate(transaction_date, from_currency, table_code = 'c', rate_type = 'ask')

			# throw an error if unable to get the rate
			if value == None:
				raise Exception(_("Getting exchange rate from NBP failed!"))

			# ------------ end of custom code ----------------

			# expire in 6 hours
			cache.set_value(key, value, expires_in_sec=6 * 60 * 60)
		return flt(value)
	except:
		# --------- customized title --------
		frappe.log_error(title="NBP Exchange Rate")
		frappe.msgprint(_("Unable to find exchange rate for {0} to {1} for key date {2}. Please create a Currency Exchange record manually").format(from_currency, to_currency, transaction_date))
		return 0.0


def get_nbp_exchange_rate(date, currency_code, table_code = 'A', rate_type = 'MID'):

	r = requests.get('https://api.nbp.pl/api/exchangerates/rates/{0}/{1}/{2}/'.format(table_code, currency_code, date))

	# if there is no rate posted on the date, api.nbp.pl returns 404
	# so get previous day
	if r.status_code == 404:
		return get_nbp_exchange_rate(get_previous_day(date), currency_code, table_code, rate_type)

	if r.status_code != 200:
		return None

	j = r.json()

	rates = j['rates']

	for rate in rates:
		return str(rate[rate_type.lower()])


def get_previous_day(date_string):
	"""
	Returns previous day as date in ISO format (string)

	params:
	- date_string (string): date in ISO format (YYYY-MM-DD)
	"""

	# python 3.7 introduced datetime.fromisoformat()
	# below code works in versions below 3.7
	# possible other solutions native to ERPNext

	d = date_string.split('-')
	year = int(d[0])
	month = int(d[1])
	day = int(d[2])

	date = datetime.date(year, month, day)
	previous_day = date - datetime.timedelta(1)

	return previous_day.isoformat()

