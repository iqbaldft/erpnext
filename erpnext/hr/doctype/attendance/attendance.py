# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import getdate, nowdate
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
					self.set_attendance_status("Half Day")
					frappe.msgprint(_("Employee {0} on Half day on {1}").format(self.employee, self.attendance_date))
				else:
					self.set_attendance_status("On Leave")
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
		from erpnext.controllers.status_updater import validate_status
		validate_status(self.get_attendance_status(), ["Present", "Absent", "On Leave", "Half Day"])
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.check_leave_record()
		self.validate_status()
		self.validate_attendance_status()

	def get_attendance_status(self):
		attendance_status = frappe.get_cached_value("Attendance Status", self.status, "attendance_status")
		return attendance_status

	def autostatus(self):
		# TODO set status based on attendance rule
		pass
	
	def set_attendance_status(self, attendance_status):
		hr_settings = frappe.get_cached_doc("HR Settings")
		if attendance_status == "Present":
			if hr_settings.default_present_status:
				self.status = hr_settings.default_present_status
			else:
				frappe.throw(_("Please set Default Present Status in HR Settings"))
		elif attendance_status == "Half Day":
			if hr_settings.default_half_day_status:
				self.status = hr_settings.default_half_day_status
			else:
				frappe.throw(_("Please set Default Half Day Status in HR Settings"))
		elif attendance_status == "On Leave":
			if hr_settings.default_on_leave_status:
				self.status = hr_settings.default_on_leave_status
			else:
				frappe.throw(_("Please set Default On Leave Status in HR Settings"))
		elif attendance_status == "Absent":
			if hr_settings.default_absent_status:
				self.status = hr_settings.default_absent_status
			else:
				frappe.throw(_("Please set Default Absent Status in HR Settings"))
		else:
			frappe.throw(_("Invalid attendance status"))
	
	def validate_attendance_status(self):
		attendance_status = frappe.get_cached_doc("Attendance Status", self.status)
		if attendance_status.docstatus != 1:
			frappe.throw(_("Attendance Status must be submitted"))
		if attendance_status.disabled == 1:
			frappe.throw(_("Attendance Status is disabled"))

	def validate_status(self):
		if not self.status:
			frappe.throw(_("Status must not be empty"))

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