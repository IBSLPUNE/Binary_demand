import frappe
from frappe.utils import flt

from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

TARGET_UOMS = {"TH Impressions", "Mn Impressions", "Bn Impressions"}

MULT = {
    "TH Impressions": 1000,
    "Mn Impressions": 1000000,
    "Bn Impressions": 1000000000,
}

# Adjust if your Currency columns support higher/lower
MAX_CURRENCY = 9999999999.99


class CustomSalesOrder(SalesOrder):
    def calculate_taxes_and_totals(self):
        """
        Override ERPNext calculation so *its own* totals always use:
        amount = (rate/1000) * qty   for TH/Mn/Bn Impressions
        """
        original_rate = {}
        original_uom = {}
        original_cf = {}
        original_stock_qty = {}

        # 1) Pre-process rows (make qty + temp effective rate)
        for row in self.items:
            uom = (row.uom or "").strip()

            if uom in TARGET_UOMS:
                # qty from impressions (keep integer to avoid "fraction" issues)
                imp = flt(row.custom_no_of_impression)
                qty = int(round(imp * MULT[uom]))

                row.qty = qty

                # prevent stock_qty overflow due to conversion_factor
                original_cf[row.name] = row.conversion_factor
                original_stock_qty[row.name] = row.stock_qty

                row.conversion_factor = 1
                row.stock_qty = qty

                # kill margin logic (your payload has margin_type="Amount")
                row.margin_type = ""
                row.margin_rate_or_amount = 0
                row.rate_with_margin = 0
                row.base_rate_with_margin = 0

                # temporarily convert rate -> effective_rate for ERPNext calc
                original_rate[row.name] = row.rate
                row.rate = flt(row.rate) / 1000.0

                # (optional) keep uom unchanged; no need to touch it
                original_uom[row.name] = row.uom

        # 2) Run standard ERPNext calculation (now it uses effective rate)
        super().calculate_taxes_and_totals()

        # 3) Restore rate for display, keep calculated totals
        for row in self.items:
            if row.name in original_rate:
                row.rate = original_rate[row.name]

            if row.name in original_cf:
                # keep conversion_factor=1 and stock_qty=qty to avoid future overflow
                row.conversion_factor = 1
                row.stock_qty = row.qty

            # taxable_value + gross_profit same as amount (your requirement)
            uom = (row.uom or "").strip()
            if uom in TARGET_UOMS:
                row.taxable_value = flt(row.amount)
                row.gross_profit = flt(row.amount)

        # 4) Overflow protection BEFORE DB write
        if flt(self.base_total) > MAX_CURRENCY:
            frappe.throw(
                f"Out of range: base_total = {flt(self.base_total):,.2f} exceeds {MAX_CURRENCY:,.2f}. "
                f"Reduce impressions or rate."
            )

