from trytond.model import MatchMixin, ModelSQL, ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import  Transaction



class AccountInvoiceAccountRule(ModelSQL, ModelView):
    """" Account Invoice Account Rule """
    __name__ = 'account.invoice.account.rule'

    name = fields.Char('Name')
    company = fields.Many2One('company.company', 'Company')
    lines = fields.One2Many('account.invoice.account.rule.line', 'rule', 'Lines')

    @staticmethod
    def default_company():
        return Transaction().context.get('company') or None

class AccountInvoiceAccountRuleLine(ModelSQL, ModelView, MatchMixin):
    """" Account Invoice Account Rule Line"""
    __name__ = 'account.invoice.account.rule.line'

    rule = fields.Many2One('account.invoice.account.rule', 'Rule')
    origin_account = fields.Many2One('account.account', 'Origin Account',
        domain=[('type', '!=', 'view')])
    target_account = fields.Many2One('account.account', 'Target Account',
      domain=[('type', '!=', 'view')])
    company = fields.Many2One('company.company', 'Company')

    def match(self, pattern):
        if 'origin_account' in pattern and pattern['origin_account'] == self.origin_account:
            return self.target_account

    @staticmethod
    def default_company():
        return Transaction().context.get('company') or None

class AccountInvoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    ruleset = fields.Many2One('account.invoice.account.rule', 'Account Rules')


    @classmethod
    def post(cls, invoices):
        Line = Pool().get('account.invoice.line')
        to_save = []
        for invoice in invoices:
            for line in invoice.lines:
                rule = line._get_account_matching_rule()
                if not rule:
                    continue
                line.account = rule.target_account
                line.on_change_account()
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

    def _get_account_matching_rule(self, pattern=None):
        RuleSet = Pool().get('account.invoice.account.rule')
        rulesets = RuleSet.search([])
        if not rulesets:
            return

        ruleset = rulesets[0]
        pattern = self._get_account_rule_pattern()
        for rule in ruleset.lines:
            if rule.match(pattern):
                return rule


