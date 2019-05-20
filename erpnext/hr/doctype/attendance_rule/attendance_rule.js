// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Rule', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__("Assign Attendance Rule"), function(){
				let doc = frappe.model.get_new_doc("Attendance Rule Assignment");
				doc.attendance_rule = frm.doc.name;
				doc.company = frm.doc.company;
				frappe.set_route("Form", "Attendance Rule Assignment", doc.name);
			});
			frm.add_custom_button(__("Assign to Employees"), function(){
				frm.trigger("assign_to_employee");
			})
		}
	},
	assign_to_employee: function(frm){
		var d = new frappe.ui.Dialog({
			title: __("Assign to Employees"),
			fields: [
				{
					fieldname: "sec_break",
					fieldtype: "Section Break",
					label: __("Filter Employees By (Optional)")
				}, {
					fieldname: 'department',
					fieldtype: 'Link',
					options: 'Department',
					label: __('Department')
				}, {
					fieldname: "employee",
					fieldtype: "Link",
					options: "Employee",
					label: __("Employee")
				},
				{
					fieldname: 'from_date',
					fieldtype: 'Date',
					label: __('From Date'),
					"reqd": 1
				},
			],
			primary_action: function(){
				var data = d.get_values();
				frappe.call({
					doc: frm.doc,
					method: "assign_attendance_rule",
					args: data,
					callback: function(r){
						if(!r.exc){
							d.hide();
							frm.reload_doc();
						}
					}
				});
			},
			primary_action_label: __("Assign")
		});
		d.show();
	}
});
