// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');

cur_frm.cscript.onload = function(doc, cdt, cdn) {
	if(doc.__islocal) cur_frm.set_value("attendance_date", frappe.datetime.get_today());
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}	
}

frappe.ui.form.on('Attendance', {
	refresh: function(frm) {

	},
	employee: function(frm){
		if(frm.doc.employee && frm.doc.attendance_date){
			frappe.call({
				method: "erpnext.hr.doctype.attendance.attendance.get_attendance_rule",
				args: {
					"employee": frm.doc.employee,
					"attendance_date": frm.doc.attendance_date
				},
				callback: function(r){
					if(r.message){
						frm.set_value("attendance_rule", r.message)
					}
				}
			});
		}
	},
	attendance_date: function(frm){
		frm.trigger("employee");
	},
	check_in_time: function(frm){
		frm.set_value("status", "");
	},
	check_out_time: function(frm){
		frm.set_value("status", "");
	}
});
