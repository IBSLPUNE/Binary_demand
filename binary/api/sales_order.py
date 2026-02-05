import frappe

TARGET_UOMS = {"TH Impressions", "Mn Impressions", "Bn Impressions"}

UOM_MULTIPLIER = {
    "TH Impressions": 1000,
    "Mn Impressions": 1000000,
    "Bn Impressions": 1000000000,
}

MAX_CURRENCY = 999999999999999999999999.99

def _f(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0

def _apply(doc):
    total_qty = 0.0
    total_amount = 0.0

    for row in doc.items:
        uom = (row.uom or "").strip()

        # kill margin logic completely (your payload shows margin_type=Amount)
        row.margin_type = ""
        row.margin_rate_or_amount = 0
        row.rate_with_margin = 0
        row.base_rate_with_margin = 0

        if uom in TARGET_UOMS:
            imp = _f(row.custom_no_of_impression)
            qty = imp * UOM_MULTIPLIER[uom]

            row.qty = qty
            row.conversion_factor = 1
            row.stock_qty = qty

            rate = _f(row.rate)
            eff_rate = rate / 1000.0
            amount = qty * eff_rate

            if amount > MAX_CURRENCY:
                frappe.throw(
                    f"Row {row.idx}: Out of range.\n"
                    f"Amount=(rate/1000)*qty = {amount:,.2f} exceeds {MAX_CURRENCY:,.2f}.\n"
                    f"Reduce impressions or rate."
                )

            # force row values
            row.amount = amount
            row.base_amount = amount
            row.net_amount = amount
            row.base_net_amount = amount
            row.net_rate = eff_rate
            row.base_net_rate = eff_rate
            row.taxable_value = amount
            row.gross_profit = amount

        total_qty += _f(row.qty)
        total_amount += _f(row.amount)

    # force doc totals
    if total_amount > MAX_CURRENCY:
        frappe.throw(
            f"Out of range: base_total would be {total_amount:,.2f} exceeds {MAX_CURRENCY:,.2f}.\n"
            f"Reduce impressions or rate."
        )

    doc.total_qty = total_qty

    doc.total = total_amount
    doc.base_total = total_amount

    doc.net_total = total_amount
    doc.base_net_total = total_amount

    # keep taxes safe
    doc.total_taxes_and_charges = _f(doc.total_taxes_and_charges)
    doc.base_total_taxes_and_charges = _f(doc.base_total_taxes_and_charges)

    doc.grand_total = total_amount + doc.total_taxes_and_charges
    doc.base_grand_total = total_amount + doc.base_total_taxes_and_charges

    doc.rounding_adjustment = 0
    doc.base_rounding_adjustment = 0
    doc.rounded_total = doc.grand_total
    doc.base_rounded_total = doc.base_grand_total


def apply_impressions_pricing(doc, method=None):
    """
    LAST-WRITER-WINS:
    ERPNext recalculates totals inside validate, so we re-apply at the end.
    """
    # avoid infinite recursion
    if getattr(doc, "_binary_lock", False):
        return
    doc._binary_lock = True

    # Apply once
    _apply(doc)

    # Apply again (important): after any other validate hooks/tax recompute
    _apply(doc)

    doc._binary_lock = False
