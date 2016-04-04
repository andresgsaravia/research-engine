# Handling incoming email

import logging, webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

ADMIN_EMAIL = "admin@research-engine.appspotmail.com"

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("INBOUND MAIL: Received a message from: %s" % mail_message.sender)
        for b in mail_message.bodies():
            logging.info("INBOUND MAIL: Body: %s" % b[1].decode())

app = webapp2.WSGIApplication([LogSenderHandler.mapping()],
                              debug = True)
