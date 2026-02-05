import frappe

def _upsert_ps(doc_type, field_name, prop, value, prop_type):
    # Property Setter primary key/name pattern: <DocType>-<field>-<property>
    name = f"{doc_type}-{field_name}-{prop}"

    if frappe.db.exists("Property Setter", name):
        ps = frappe.get_doc("Property Setter", name)
        ps.value = str(value)
        ps.property_type = prop_type
        ps.doctype_or_field = "DocField"
        ps.save(ignore_permissions=True)
        return

    frappe.get_doc({
        "doctype": "Property Setter",
        "name": name,
        "doc_type": doc_type,
        "field_name": field_name,
        "property": prop,
        "value": str(value),
        "property_type": prop_type,
        "doctype_or_field": "DocField",
    }).insert(ignore_permissions=True)

def execute():
    # Increase numeric field capacity in Sales Order (header totals)
    fields = [
        "total_qty",
        "total",
        "base_total",
        "net_total",
        "base_net_total",
        "grand_total",
        "base_grand_total",
        "rounded_total",
        "base_rounded_total",
        "total_taxes_and_charges",
        "base_total_taxes_and_charges",
    ]

    for f in fields:
        _upsert_ps("Sales Order", f, "length", 21, "Int")
        _upsert_ps("Sales Order", f, "precision", 9, "Int")

    # Item row amounts too (important)
    item_fields = [
        "amount", "base_amount",
        "net_amount", "base_net_amount",
        "taxable_value",
        "gross_profit",
    ]
    for f in item_fields:
        _upsert_ps("Sales Order Item", f, "length", 21, "Int")
        _upsert_ps("Sales Order Item", f, "precision", 9, "Int")
