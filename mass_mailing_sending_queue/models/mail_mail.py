# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _postprocess_sent_message(self, cr, uid, mail, context=None,
                                  mail_sent=True):
        # Read before super, because mail will be removed if sent successfully
        stats = mail.statistics_ids
        res = super(MailMail, self)._postprocess_sent_message(
            cr, uid, mail, context=context, mail_sent=mail_sent)
        if stats:
            for stat in stats:
                if stat.mass_mailing_sending_id.state == 'sending':
                    stat.mass_mailing_sending_id._process_sending()
        return res
