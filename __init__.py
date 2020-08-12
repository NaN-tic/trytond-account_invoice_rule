# This file is part account_invoice_rule module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
def register():
    Pool.register(
        invoice.AccountInvoice,
        invoice.AccountInvoiceLine,
        invoice.AccountInvoiceAccountRule,
        invoice.AccountInvoiceAccountRuleLine,
        invoice.Party,
        invoice.PartyAccount,
        module='account_invoice_rule', type_='model')
