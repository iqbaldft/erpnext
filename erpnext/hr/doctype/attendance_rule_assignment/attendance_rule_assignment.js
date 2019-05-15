// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Rule Assignment', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		frm.set_query("attendance_rule", function(){
			return {
				"filters": {
					"docstatus": 1,
					"company": frm.doc.company,
					"disabled": 0
				}
			};
		});
	}
});
