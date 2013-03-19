# Here we hold and generatethe texts for emails. 
# Perhaps later this will be a little smarter...

from google.appengine.api import mail
from google.appengine.ext import db

###########################
##   Datastore Objects   ##
###########################

# Each Notification should have as parent a RegisteredUser
class Notifications(db.Model):
    author = db.ReferenceProperty(required = False)
    category = db.StringProperty(required = True)
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    link = db.StringProperty(required = False)
    sent = db.BooleanProperty(required = True)
        


ADMIN_EMAIL = "admin@research-engine.appspot.com"


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
        
