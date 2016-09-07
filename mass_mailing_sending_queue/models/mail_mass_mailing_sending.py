# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class MailMassMailingSending(models.Model):
    _name = 'mail.mass_mailing.sending'

    state = fields.Selection([
        ('enqueued', "Enqueued"),
        ('sending', "Sending"),
        ('sent', "Sent"),
    ], string="State", required=True, copy=False, default='enqueued')
    mass_mailing_id = fields.Many2one(
        string="Mass mailing", comodel_name='mail.mass_mailing', readonly=True)
    pending = fields.Integer(
        string="Recipients pending", compute='_compute_pending')
    sending = fields.Integer(
        string="Emails sending", compute='_compute_sending')
    sent = fields.Integer(
        string="Emails sent", compute='_compute_sent')
    failed = fields.Integer(
        string="Emails failed", compute='_compute_failed')

    def _batch_size_default(self):
        return 500

    def _batch_size_get(self):
        m_param = self.env['ir.config_parameter']
        batch_size = self._batch_size_default()
        batch_size_str = m_param.get_param(
            'mail.mass_mailing.sending.batch_size')
        if batch_size_str and batch_size_str.isdigit():
            batch_size = int(batch_size_str)
        return batch_size

    @api.multi
    def pending_recipients(self):
        self.ensure_one()
        res_ids = self.mass_mailing_id.get_recipients(self.mass_mailing_id)
        already_enqueued = self.env['mail.mail.statistics'].search([
            ('mass_mailing_sending_id', '=', self.id),
        ])
        pending_ids = list(
            set(res_ids) - set(already_enqueued.mapped('res_id')))
        return pending_ids

    @api.multi
    def get_recipients(self):
        self.ensure_one()
        batch_size = self._batch_size_get()
        pending_ids = self.pending_recipients()
        return pending_ids[:batch_size]

    @api.multi
    def send_mail(self):
        # Refactoring same process from here using v8 API:
        # mass_mailing/models/mass_mailing.py:597:send_mail()
        for sending in self:
            res_ids = sending.get_recipients()
            if not res_ids:  # pragma: no cover
                continue
            m_compose = sending.env['mail.compose.message'].\
                with_context(active_ids=res_ids,
                             mass_mailing_sending_id=sending.id)
            mailing = sending.mass_mailing_id
            attachments = [(4, att.id) for att in mailing.attachment_ids]
            mailing_lists = [(4, l.id) for l in mailing.contact_list_ids]
            data = {
                'author_id': self.env.user.partner_id.id,
                'attachment_ids': attachments,
                'body': mailing.body_html,
                'subject': mailing.name,
                'model': mailing.mailing_model,
                'email_from': mailing.email_from,
                'record_name': False,
                'composition_mode': 'mass_mail',
                'mass_mailing_id': mailing.id,
                'mailing_list_ids': mailing_lists,
                'no_auto_thread': mailing.reply_to_mode != 'thread',
            }
            if mailing.reply_to_mode == 'email':
                data['reply_to'] = mailing.reply_to
            composer_id = m_compose.create(data)
            composer_id.send_mail()

    def _process_enqueued(self):
        # Create mail_mail objects not created
        if self.pending_recipients():
            self.send_mail()
        # If there is no more recipient left, mark as sending
        if not self.pending_recipients():
            self.state = 'sending'

    def _process_sending(self):
        # Check if there is any mail_mail object not sent
        pending_emails = self.env['mail.mail.statistics'].search([
            ('mass_mailing_sending_id', '=', self.id),
            ('scheduled', '!=', False),
            ('sent', '=', False),
            ('exception', '=', False),
        ])
        if not pending_emails:
            self.mass_mailing_id.write({
                'state': 'done',
            })
            self.state = 'sent'

    def _process(self):
        self.ensure_one()
        method = getattr(self, '_process_%s' % self.state, None)
        if method and hasattr(method, '__call__'):
            return method()
        return False  # pragma: no cover

    @api.model
    def sendings_running(self):
        return self.search([
            ('state', 'in', ('enqueued', 'sending')),
        ])

    @api.model
    def cron(self):
        # Process all mail.mass_mailing.sending in enqueue or sending state
        sendings = self.sendings_running()
        for sending in sendings:
            _logger.info("Sending [%d] mass mailing [%d] '%s' (%s)",
                         sending.id, sending.mass_mailing_id.id,
                         sending.mass_mailing_id.name, sending.state)
            sending._process()
        return True

    @api.multi
    def _compute_pending(self):
        for sending in self:
            sending.pending = 0
            if sending.state == 'enqueued':
                sending.pending = len(sending.pending_recipients())

    @api.multi
    def _compute_sending(self):
        m_stats = self.env['mail.mail.statistics']
        for sending in self:
            sending.sending = 0
            if sending.state in {'enqueued', 'sending'}:
                sending.sending = m_stats.search_count([
                    ('mass_mailing_sending_id', '=', sending.id),
                    ('scheduled', '!=', False),
                    ('sent', '=', False),
                    ('exception', '=', False),
                ])

    @api.multi
    def _compute_sent(self):
        m_stats = self.env['mail.mail.statistics']
        for sending in self:
            sending.sent = m_stats.search_count([
                ('mass_mailing_sending_id', '=', sending.id),
                ('scheduled', '!=', False),
                ('sent', '!=', False),
                ('exception', '=', False),
            ])

    @api.multi
    def _compute_failed(self):
        m_stats = self.env['mail.mail.statistics']
        for sending in self:
            sending.failed = m_stats.search_count([
                ('mass_mailing_sending_id', '=', sending.id),
                ('scheduled', '!=', False),
                ('exception', '!=', False),
            ])
