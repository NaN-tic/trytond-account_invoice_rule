from trytond.model import MatchMixin, ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval

class AccountInvoiceAccountRule(ModelSQL, ModelView):
    """Account Invoice Account Rule"""
    __name__ = 'account.invoice.account.rule'

    name = fields.Char('Name', required=True)
    company = fields.Many2One('company.company', 'Company', required=True)
    lines = fields.One2Many('account.invoice.account.rule.line', 'rule', 'Lines',
        domain=[('company', '=', Eval('company'))])

    @staticmethod
    def default_company():
        return Transaction().context.get('company') or None

    def compute(self, pattern):
        for line in self.lines:
            if line.match(pattern):
                return line.target_account

        return pattern.get('origin_account')


class AccountInvoiceAccountRuleLine(ModelSQL, ModelView, MatchMixin):
    """Account Invoice Account Rule Line"""
    __name__ = 'account.invoice.account.rule.line'

    rule = fields.Many2One('account.invoice.account.rule', 'Rule', required=True, ondelete='CASCADE')
    origin_account = fields.Many2One('account.account', 'Origin Account',
        domain=[
            ('type', '!=', 'view'),
            ('company', '=', Eval('_parent_rule', {}).get('company', -1)),
            ], required=True)
    target_account = fields.Many2One('account.account', 'Target Account',
      domain=[
            ('type', '!=', 'view'),
            ('company', '=', Eval('_parent_rule', {}).get('company', -1)),
            ], required=True)
    company = fields.Function(fields.Many2One('company.company', 'Company'),
        'on_change_with_company', searcher='search_company')

    def match(self, pattern):
        if 'origin_account' in pattern and pattern['origin_account'] == self.origin_account:
            return True
        return False

    @fields.depends('rule', '_parent_rule.company')
    def on_change_with_company(self, name=None):
        if self.rule:
            return self.rule.company.id
        return Transaction().context.get('company') or None

    @classmethod
    def search_company(cls, name, clause):
        return [('rule.%s' % name,) + tuple(clause[1:])]


class AccountInvoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def post(cls, invoices):
        Line = Pool().get('account.invoice.line')
        to_save = []
        for invoice in invoices:
            if invoice.move:
                continue
            rule = invoice.party.customer_invoice_account_rule
            if invoice.type == 'in':
                rule = invoice.party.supplier_invoice_account_rule
            if not rule:
                continue
            for line in invoice.lines:
                pattern = line._get_account_rule_pattern()
                new_account = rule.compute(pattern)
                if not new_account or line.account == new_account:
                    continue
                line.account = rule.compute(pattern)
                to_save.append(line)
        Line.save(to_save)
        super().post(invoices)


class AccountInvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    def _get_account_rule_pattern(self, pattern=None):
        if pattern is None:
            pattern = {}
        else:
            pattern = pattern.copy()
        pattern['origin_account'] = self.account
        return pattern


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    customer_invoice_account_rule = fields.MultiValue(fields.Many2One(
            'account.invoice.account.rule', "Customer Invoice Account Rule",
            domain=[('company', '=', Eval('context', {}).get('company', -1)),],
            ))
    supplier_invoice_account_rule = fields.MultiValue(fields.Many2One(
            'account.invoice.account.rule', "Supplier Invoice Account Rule",
            domain=[('company', '=', Eval('context', {}).get('company', -1)),]))


    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'customer_invoice_account_rule', 'supplier_invoice_account_rule'}:
            return pool.get('party.party.account')
        return super(Party, cls).multivalue_model(field)


class PartyAccount(metaclass=PoolMeta):
    """Party Account"""
    __name__ = 'party.party.account'

    customer_invoice_account_rule = fields.Many2One(
            'account.invoice.account.rule', "Customer Invoice Account Rule",
            domain=[('company', '=', Eval('company', -1)),])
    supplier_invoice_account_rule = fields.Many2One(
            'account.invoice.account.rule', "Supplier Invoice Account Rule",
            domain=[('company', '=', Eval('company', -1)),
            ])
