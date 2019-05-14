# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

from frappe.model.document import Document

class HRSettings(Document):
	def validate(self):
		from erpnext.setup.doctype.naming_series.naming_series import set_by_naming_series
		set_by_naming_series("Employee", "employee_number",
			self.get("emp_created_by")=="Naming Series", hide_name_field=True)
		self.validate_default_attendance_status()

	def validate_default_attendance_status(self):
		def validate_status(field_status, expected):
			if not field_status:
				return
			status = frappe.get_cached_value("Attendance Status", field_status, "attendance_status")
			if status != expected:
				frappe.throw("{} {}".format(_("Invalid attendance status:"), field_status))
		validate_status(self.default_present_status, "Present")
		validate_status(self.default_half_day_status, "Half Day")
		validate_status(self.default_on_leave_status, "On Leave")
		validate_status(self.default_absent_status, "Absent")
