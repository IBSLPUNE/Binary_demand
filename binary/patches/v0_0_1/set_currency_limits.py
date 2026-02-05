import frappe

def execute():
    targets = [
        ("Sales Order", [
            "total","base_total",
            "net_total","base_net_total",
            "grand_total","base_grand_total",
            "rounded_total","base_rounded_total",
            "total_taxes_and_charges","base_total_taxes_and_charges",
        ]),
        ("Sales Order Item", [
            "amount","base_amount",
            "net_amount","base_net_amount",
            "taxable_value","gross_profit",
        ]),
    ]

    for dt, fields in targets:
        for f in fields:
            frappe.db.sql("""
                UPDATE `tabDocField`
                SET `length` = 30, `precision` = 9
                WHERE `parent` = %s AND `fieldname` = %s
            """, (dt, f))

    frappe.clear_cache()
