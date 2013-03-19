# Here we hold and generatethe texts for emails. 
# Perhaps later this will be a little smarter...

from google.appengine.api import mail
from google.appengine.ext import db
from generic import *

ADMIN_EMAIL = "admin@research-engine.appspot.com"


######################
##   Web Handlers   ##
######################

class SendNotifications(GenericPage):
    def get(self):
        logging.debug("CRON: Handler %s has been requested by cron" % self.__class__.__name__)
        for u in RegisteredUsers.all().run():
            notifications_list = []
            for n in EmailNotifications.all().ancestor(u).filter("sent =", False).order("date").run():
                notifications_list.append(n)
            send_notifications(notifications_list, u)
        self.write("Done")


##########################
##   Helper Functions   ##
##########################

def send_notifications(notifications_list, user):
    message = mail.EmailMessage(sender = ADMIN_EMAIL,
                                to = user.email,
                                subject = "Recent activity in your projects",
                                body = render_str("notification_email.txt", 
                                                  notifications_list = notifications_list, user = user),
                                html = render_str("notification_email.html", 
                                                  notifications_list = notifications_list, user = user))
    logging.debug("EMAIL: Sending an email with notifications to user %s" % user.username)
    message.send()
    for n in notifications_list:
        n.sent = True
        logging.debug("DB WRITE: CRON: Changing a notification's 'sent' property to true")
        n.put()
    return


def send_verify_email(user):
    link = "http://research-engine.appspot.com/verify_email?username=%s&h=%s" % (user.username, hash_str(user.username + user.salt))
    message = verify_email_message(link)
    message.to = user.email
    logging.debug("EMAIL: Sending an email verification request.")
    message.send()
    return


SIGNATURE = """
-----------------------------------
Research Engine <admin@research-engine.appspot.com>"""


SIGNATURE_HTML = """<br/>
-----------------------------------<br/>
<a href="http://research-engine.appspot.com">Research Engine</a> &lt;<a href="mailto:admin@research-engine.appspot.com">admin@research-engine.appspot.com</a>&gt;"""


def verify_email_message(verify_link):
    body = """
We received a request to create a new account on our website with this email address. If you made this request please visit the following link to confirm your email:
%s
If you didn't made this request, please ignore this email.
""" % verify_link
    body += SIGNATURE

    html = """
We received a request to create a new account on our website with this email address. If you made this request please visit the following link to confirm your email by clicking the following link:<br/><br/>
<a href="%s">%s</a><br/><br/>
If you didn't made this request, please ignore this email.
""" % (verify_link, verify_link)
    html += SIGNATURE_HTML

    message = mail.EmailMessage(sender = ADMIN_EMAIL,
                                subject = "Email verification.",
                                body = body,
                                html = html)
    return message
        
