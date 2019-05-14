// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('HR Settings', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		frm.set_query("default_present_status", function(){
			return {
				"filters": {
					"attendance_status": "Present"
				}
			};
		});
		frm.set_query("default_half_day_status", function(){
			return {
				"filters": {
					"attendance_status": "Half Day"
				}
			};
		});
		frm.set_query("default_on_leave_status", function(){
			return {
				"filters": {
					"attendance_status": "On Leave"
				}
			};
		});
		frm.set_query("default_absent_status", function(){
			return {
				"filters": {
					"attendance_status": "Absent"
				}
			};
		});
	}
});
