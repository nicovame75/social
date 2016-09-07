# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class MailMassMailingSending(models.Model):
    _inherit = 'mail.mass_mailing'

    state = fields.Selection(selection_add=[
        ('sending', "Sending"),
    ])
    pending = fields.Integer(string="Pending", compute='_compute_pending')

    @api.multi
    def send_mail(self):
        # Override 'Send to All' button completly.
        # NOTE: Please, notice that this breaks inheritance chain
        for mailing in self:
            res_ids = mailing.get_recipients(mailing)
            if not res_ids:
                raise UserError(_("Please select recipients."))
            self.env['mail.mass_mailing.sending'].create({
                'state': 'enqueued',
                'mass_mailing_id': mailing.id,
            })
            mailing.write({
                'sent_date': fields.datetime.now(),
                'state': 'sending',
            })
        return True

    @api.multi
    def _compute_pending(self):
        for mailing in self:
            self.pending = 0
            sendings = self.env['mail.mass_mailing.sending'].search([
                ('mass_mailing_id', '=', mailing.id),
                ('state', '=', 'enqueued'),
            ])
            self.pending = sum(sendings.mapped('pending'))
