.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==========================
Mass mailing sending queue
==========================

This module adds a sending queue when mass mailing 'Send to All' button is
clicked. This is an aditional queue, there is another one for sending emails.


Usage
=====

When 'Send to All' button is clicked al mass mailing form, all 'mail.mail'
and 'mail.mail.statistics' objects are created. This process shall take
so much time if recipient list is 10k+ and the famous
"Take a minute to get a coffee, because it's loading..." text appears.

With this new queue user will see that mass mailing is in 'Sending' state until
all emails are sent or failed. Screen will return to mass mailing form
immediately after 'Send to All' button is clicked.

In 'Settings > Technical > Email > Mass mailing sending' admin can monitorize
all running mass mailing sending objects and see

* Recipients pending: How many recipients have no email created yet
* Emails sending: How many emails are created and not sent yet
* Emails sent: How many emails have been sent successfully
* Emails failed: How many emails couldn't be sent because an error occurred


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/205/8.0


Known issues / Roadmap
======================

**WARNING**: This addon breaks inheritance chain of
'mail.mass_mailing.send_mail' method


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/social/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Antonio Espinosa <antonio.espinosa@tecnativa.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
