# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from copy import deepcopy
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
import logging


class MailMassMailing(models.Model):
    _inherit = 'mail.mass_mailing'

    state = fields.Selection(selection_add=[
        ('sending', "Sending"),
    ])
    pending = fields.Integer(string="Pending", compute='_compute_pending')
    mass_mailing_sending_ids = fields.One2many(
        comodel_name='mail.mass_mailing.sending', readonly=True,
        inverse_name='mass_mailing_id', string="Sending tasks")

    def read_group(self, cr, uid, domain, fields, groupby, **kwargs):
        res = super(MailMassMailing, self).read_group(
            cr, uid, domain, fields, groupby, **kwargs)
        if groupby and groupby[0] == "state":
            group_domain = domain + [('state', '=', 'sending')]
            count = self.search_count(
                cr, uid, group_domain, context=kwargs.get('context', {}))
            res.append({
                '__context': {'group_by': groupby[1:]},
                '__domain': group_domain,
                'state': ('sending', _("Sending")),
                'state_count': count,
            })
        return res

    def _sendings_get(self):
        self.ensure_one()
        return self.env['mail.mass_mailing.sending'].search([
            ('mass_mailing_id', '=', self.id),
            ('state', 'in', ('enqueued', 'sending')),
        ])

    @api.multi
    def send_mail(self):
        if self.env.context.get('sending_queue_enabled', False):
            for mailing in self:
                m_sending = self.env['mail.mass_mailing.sending']
                sendings = mailing._sendings_get()
                if sendings:
                    raise UserError(_(
                        "There is another sending task running. "
                        "Please, be pacient. You can see all sending tasks in "
                        "'Sending tasks' tab"
                    ))

                res_ids = mailing.get_recipients(mailing)
                batch_size = m_sending.batch_size_get()
                if not res_ids:
                    raise UserError(_("Please select recipients."))
                sending = m_sending.create({
                    'state': 'draft',
                    'mass_mailing_id': mailing.id,
                })
                sending_state = 'enqueued'
                if len(res_ids) < (batch_size / 2):
                    mailing.with_context(
                        mass_mailing_sending_id=sending.id,
                        sending_queue_enabled=False).send_mail()
                    sending_state = 'sending'
                sending.state = sending_state
                mailing.write({
                    'sent_date': fields.datetime.now(),
                    'state': 'sending',
                })
            return True
        return super(MailMassMailing, self).send_mail()

    @api.model
    def get_recipients(self, mailing):
        res_ids = super(MailMassMailing, self).get_recipients(mailing)
        sending_id = self.env.context.get('mass_mailing_sending_id', False)
        if sending_id:
            sending = self.env['mail.mass_mailing.sending'].browse(sending_id)
            res_ids = sending.get_recipient_batch(res_ids)
        return res_ids

    @api.multi
    def _compute_pending(self):
        for mailing in self:
            sendings = mailing._sendings_get()
            self.pending = (
                sum(sendings.mapped('pending')) +
                sum(sendings.mapped('sending')))
