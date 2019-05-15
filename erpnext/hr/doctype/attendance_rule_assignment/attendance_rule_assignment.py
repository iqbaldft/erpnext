# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class AttendanceRuleAssignment(Document):
	pass


def get_attendance_rule(employee, from_date, company=None, department=None, not_found_error=False):
	filters={
		"employee": employee,
		"from_date": ["<=", from_date],
		"company": company or frappe.get_value("Employee", employee, "company")
	}
	if department:
		filters["department"] = department
	attendance_rule = frappe.get_all("Attendance Rule", filters=filters, order_by="from_date desc")
	if len(attendance_rule) > 0:
		return attendance_rule[0].attendance_rule
	elif not_found_error:
		frappe.throw(_("Attendance rule not found for employee {0} from date {1}").format(employee, from_date))
	else:
		return None

