# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.exceptions import Warning as UserError


class TestMassMailingSending(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestMassMailingSending, self).setUp(*args, **kwargs)

        self.list = self.env['mail.mass_mailing.list'].create({
            'name': 'Test list',
        })
        self.contact_a = self.env['mail.mass_mailing.contact'].create({
            'list_id': self.list.id,
            'name': 'Test contact A',
            'email': 'contact_a@example.org',
        })
        self.contact_b = self.env['mail.mass_mailing.contact'].create({
            'list_id': self.list.id,
            'name': 'Test contact B',
            'email': 'contact_b@example.org',
        })
        self.mass_mailing = self.env['mail.mass_mailing'].create({
            'name': 'Test mass mailing',
            'email_from': 'from@example.org',
            'mailing_model': 'mail.mass_mailing.contact',
            'mailing_domain': [
                ('list_id', 'in', [self.list.id]),
                ('opt_out', '=', False),
            ],
            'contact_list_ids': [(6, False, [self.list.id])],
            'body_html': '<p>Hello world!</p>',
            'reply_to_mode': 'email',
        })

    def test_cron(self):
        self.mass_mailing.send_mail()
        sendings = self.env['mail.mass_mailing.sending'].search([
            ('mass_mailing_id', '=', self.mass_mailing.id),
        ])
        stats = self.env['mail.mail.statistics'].search([
            ('mass_mailing_id', '=', self.mass_mailing.id),
        ])
        # 1 sending in enqueued state and 0 email stats created
        self.assertEqual(1, len(sendings))
        self.assertEqual(0, len(stats))
        sending = sendings[0]
        self.assertEqual('enqueued', sending.state)
        self.assertEqual(2, sending.pending)
        self.assertEqual('sending', self.mass_mailing.state)
        self.assertEqual(2, self.mass_mailing.pending)
        # Create email stats
        sending.cron()
        stats = self.env['mail.mail.statistics'].search([
            ('mass_mailing_id', '=', self.mass_mailing.id),
        ])
        # 1 sending in sending state and 2 email stats created
        self.assertEqual(2, len(stats))
        self.assertEqual('sending', sending.state)
        self.assertEqual(2, sending.sending)
        self.assertEqual('sending', self.mass_mailing.state)
        for stat in stats:
            if stat.mail_mail_id:
                stat.mail_mail_id.send()
        # Check that all emails are already sent
        sending.cron()
        self.assertEqual('sent', sending.state)
        self.assertEqual(2, sending.sent)
        self.assertEqual(0, sending.failed)
        self.assertEqual('done', self.mass_mailing.state)

    def test_no_recipients(self):
        empty_list = self.env['mail.mass_mailing.list'].create({
            'name': 'Test list with no recipients',
        })
        mass_mailing = self.env['mail.mass_mailing'].create({
            'name': 'Test mass mailing with no recipients',
            'email_from': 'from@example.org',
            'mailing_model': 'mail.mass_mailing.contact',
            'mailing_domain': [
                ('list_id', 'in', [empty_list.id]),
                ('opt_out', '=', False),
            ],
            'contact_list_ids': [(6, False, [empty_list.id])],
            'body_html': '<p>Hello no one!</p>',
            'reply_to_mode': 'email',
        })
        with self.assertRaises(UserError):
            mass_mailing.send_mail()
