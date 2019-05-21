# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

import datetime
from frappe.utils import getdate, nowdate, get_time
from frappe import _
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name
from frappe.utils import cstr

class Attendance(Document):
	def validate_duplicate_record(self):
		res = frappe.db.sql("""select name from `tabAttendance` where employee = %s and attendance_date = %s
			and name != %s and docstatus = 1""",
			(self.employee, self.attendance_date, self.name))
		if res:
			frappe.throw(_("Attendance for employee {0} is already marked").format(self.employee))

		set_employee_name(self)

	def check_leave_record(self):
		leave_record = frappe.db.sql("""select leave_type, half_day, half_day_date from `tabLeave Application`
			where employee = %s and %s between from_date and to_date and status = 'Approved'
			and docstatus = 1""", (self.employee, self.attendance_date), as_dict=True)
		if leave_record:
			for d in leave_record:
				if d.half_day_date == getdate(self.attendance_date):
					self.set_default_attendance_status("Half Day")
					frappe.msgprint(_("Employee {0} on Half day on {1}").format(self.employee, self.attendance_date))
				else:
					self.set_default_attendance_status("On Leave")
					self.leave_type = d.leave_type
					frappe.msgprint(_("Employee {0} is on Leave on {1}").format(self.employee, self.attendance_date))

		if self.get_attendance_status() == "On Leave" and not leave_record:
			frappe.throw(_("No leave record found for employee {0} for {1}").format(self.employee, self.attendance_date))

	def validate_attendance_date(self):
		date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

		if getdate(self.attendance_date) > getdate(nowdate()):
			frappe.throw(_("Attendance can not be marked for future dates"))
		elif date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
			frappe.throw(_("Attendance date can not be less than employee's joining date"))

	def validate_employee(self):
		emp = frappe.db.sql("select name from `tabEmployee` where name = %s and status = 'Active'",
		 	self.employee)
		if not emp:
			frappe.throw(_("Employee {0} is not active or does not exist").format(self.employee))

	def validate(self):
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.check_leave_record()
		self.set_attendance_rule()

		if not self.status:
			self.autostatus()
		from erpnext.controllers.status_updater import validate_status
		validate_status(self.get_attendance_status(), ["Present", "Absent", "On Leave", "Half Day"])
		self.validate_status()
		self.validate_attendance_status()

	def get_attendance_status(self):
		if self.status:
			return frappe.get_cached_value("Attendance Status", self.status, "attendance_status")
		return None

	def set_attendance_rule(self):
		self.attendance_rule = get_attendance_rule(self.employee, self.attendance_date)

	def validate_attendance_rule(self):
		attendance_rule = frappe.get_doc("Attendance Rule", self.attendance_rule)
		if attendance_rule.disabled:
			frappe.throw(_("Attendance Rule {} is disabled").format(self.attendance_rule))

	def autostatus(self):
		data = self.get_data()
		self.eval_condition_and_status(data)

	def get_data(self):
		data = frappe._dict()
		data.update(frappe.get_doc("Attendance Rule", self.attendance_rule).as_dict())
		data.update(frappe.get_doc("Employee", self.employee).as_dict())
		data.update(self.as_dict())
		return data

	def eval_condition_and_status(self, data):
		whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": datetime.date,
			"datetime": datetime.datetime,
			"time": datetime.time,
			"getdate": getdate,
			"gettime": get_time
		}

		attendance_rule = frappe.get_cached_doc("Attendance Rule", self.attendance_rule)
		attendance_rule_condition = attendance_rule.attendance_rule_condition
		status = ""
		for row in attendance_rule_condition:
			try:
				if frappe.safe_eval(row.condition, whitelisted_globals, data):
					status = row.attendance_status
			except TypeError:
				pass
			if status:
				break
		if status:
			self.status = status
		else:
			frappe.throw(_("No suitable status assigned"))

	def get_default_attendance_status(self, attendance_status):
		hr_settings = frappe.get_cached_doc("HR Settings")
		if attendance_status == "Present":
			if hr_settings.default_present_status:
				return hr_settings.default_present_status
			else:
				frappe.throw(_("Please set Default Present Status in HR Settings"))
		elif attendance_status == "Half Day":
			if hr_settings.default_half_day_status:
				return hr_settings.default_half_day_status
			else:
				frappe.throw(_("Please set Default Half Day Status in HR Settings"))
		elif attendance_status == "On Leave":
			if hr_settings.default_on_leave_status:
				return hr_settings.default_on_leave_status
			else:
				frappe.throw(_("Please set Default On Leave Status in HR Settings"))
		elif attendance_status == "Absent":
			if hr_settings.default_absent_status:
				return hr_settings.default_absent_status
			else:
				frappe.throw(_("Please set Default Absent Status in HR Settings"))
		else:
			frappe.throw(_("Invalid attendance status"))

	def set_default_attendance_status(self, attendance_status):
		self.status = get_default_attendance_status(attendance_status)
	
	def validate_attendance_status(self):
		attendance_status = frappe.get_cached_doc("Attendance Status", self.status)
		if attendance_status.docstatus != 1:
			frappe.throw(_("Attendance Status must be submitted"))
		if attendance_status.disabled == 1:
			frappe.throw(_("Attendance Status is disabled"))

	def validate_status(self):
		if not self.status:
			frappe.throw(_("Status must not be empty"))


def get_default_attendance_status(attendance_status):
	"""
	:param attendance_status: one of "Present", "Half Day", "On Leave", or "Absent"

	:return: default attendance status set on HR Settings
	"""
	hr_settings = frappe.get_cached_doc("HR Settings")
	if attendance_status == "Present":
		if hr_settings.default_present_status:
			return hr_settings.default_present_status
		else:
			frappe.throw(_("Please set Default Present Status in HR Settings"))
	elif attendance_status == "Half Day":
		if hr_settings.default_half_day_status:
			return hr_settings.default_half_day_status
		else:
			frappe.throw(_("Please set Default Half Day Status in HR Settings"))
	elif attendance_status == "On Leave":
		if hr_settings.default_on_leave_status:
			return hr_settings.default_on_leave_status
		else:
			frappe.throw(_("Please set Default On Leave Status in HR Settings"))
	elif attendance_status == "Absent":
		if hr_settings.default_absent_status:
			return hr_settings.default_absent_status
		else:
			frappe.throw(_("Please set Default Absent Status in HR Settings"))
	else:
		frappe.throw(_("Invalid attendance status. Please select one of 'Present', 'Half Day', 'On Leave', or 'Absent'"))

@frappe.whitelist()
def get_events(start, end, filters=None):
	events = []

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})

	if not employee:
		return events

	from frappe.desk.reportview import get_filters_cond
	conditions = get_filters_cond("Attendance", filters, [])
	add_attendance(events, start, end, conditions=conditions)
	return events

def add_attendance(events, start, end, conditions=None):
	query = """select name, attendance_date, status
		from `tabAttendance` where
		attendance_date between %(from_date)s and %(to_date)s
		and docstatus < 2"""
	if conditions:
		query += conditions

	for d in frappe.db.sql(query, {"from_date":start, "to_date":end}, as_dict=True):
		e = {
			"name": d.name,
			"doctype": "Attendance",
			"date": d.attendance_date,
			"title": cstr(d.status),
			"docstatus": d.docstatus
		}
		if e not in events:
			events.append(e)

@frappe.whitelist()
def get_attendance_rule(employee, attendance_date):
	filters = {
		"employee": employee,
		"from_date": ["<=", attendance_date],
		"docstatus": 1
	}
	attendance_rule = frappe.get_all("Attendance Rule Assignment", filters=filters, fields=["name", "attendance_rule"], order_by="from_date desc", limit_page_length=1)
	if attendance_rule:
		return attendance_rule[0]["attendance_rule"]
	else:
		frappe.throw(_("Attendance Rule Assignment not found for Employee {}").format(employee))
