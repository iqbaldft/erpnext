# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class AttendanceRuleAssignment(Document):
	def validate(self):
		self.validate_attendance_rule()
		self.validate_duplicate_from_date()
	
	def validate_duplicate_from_date(self):
		filters = {
			"employee": self.employee,
			"from_date": self.from_date,
			"docstatus": 1
		}
		a_r_a = frappe.get_all("Attendance Rule Assignment", filters)
		if a_r_a:
			frappe.throw(_("Employee {0} already have assignment on {}").format(self.employee, self.from_date))

	def validate_attendance_rule(self):
		attendance_rule = frappe.get_doc("Attendance Rule", self.attendance_rule)
		if attendance_rule.company != self.company:
			frappe.throw(_("Invalid Attendance Rule selected"))
		if attendance_rule.docstatus != 1:
			frappe.throw(_("Invalid Attendance Rule selected"))
		if attendance_rule.disabled:
			frappe.throw(_("Attendance Rule is disabled"))


def get_attendance_rule(employee, from_date, company=None, department=None):
	filters={
		"employee": employee,
		"from_date": ["<=", from_date],
		"company": company or frappe.get_value("Employee", employee, "company"),
		"docstatus": 1
	}
	if department:
		filters["department"] = department
	attendance_rule = frappe.get_all("Attendance Rule", filters=filters, order_by="from_date desc")
	if len(attendance_rule) > 0:
		return attendance_rule[0].attendance_rule
	else:
		frappe.throw(_("Attendance rule not found for employee {0} from date {1}").format(employee, from_date))

