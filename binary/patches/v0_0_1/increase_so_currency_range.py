import frappe

def _upsert_ps(doc_type, field_name, prop, value, prop_type="Int"):
    # Unique by (doc_type, field_name, property)
    existing = frappe.get_all(
        "Property Setter",
        filters={"doc_type": doc_type, "field_name": field_name, "property": prop, "doctype_or_field": "DocField"},
        pluck="name",
        limit=1,
    )

    data = {
        "doctype": "Property Setter",
        "doctype_or_field": "DocField",
        "doc_type": doc_type,
        "field_name": field_name,
        "property": prop,
        "value": str(value),
        "property_type": prop_type,
    }

    if existing:
        ps = frappe.get_doc("Property Setter", existing[0])
        ps.value = str(value)
        ps.property_type = prop_type
        ps.save(ignore_permissions=True)
    else:
        frappe.get_doc(data).insert(ignore_permissions=True)

def execute():
    # Keep money decimals normal (2), increase LENGTH big so ERPNext doesn't block > 9,999,999,999.99
    # length=21 precision=2 => max 10^(19) - 0.01 (huge)
    TARGET_LENGTH = 30
    TARGET_PRECISION = 2

    # Sales Order (parent) totals
    so_currency_fields = [
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
        "base_rounding_adjustment",
        "rounding_adjustment",
        "discount_amount",
        "base_discount_amount",
    ]

    # Sales Order Item (child) amounts
    soi_currency_fields = [
        "rate",
        "base_rate",
        "amount",
        "base_amount",
        "net_rate",
        "base_net_rate",
        "net_amount",
        "base_net_amount",
        "taxable_value",
        "gross_profit",
    ]

    for f in so_currency_fields:
        _upsert_ps("Sales Order", f, "length", TARGET_LENGTH, "Int")
        _upsert_ps("Sales Order", f, "precision", TARGET_PRECISION, "Int")

    for f in soi_currency_fields:
        _upsert_ps("Sales Order Item", f, "length", TARGET_LENGTH, "Int")
        _upsert_ps("Sales Order Item", f, "precision", TARGET_PRECISION, "Int")

    frappe.clear_cache()

