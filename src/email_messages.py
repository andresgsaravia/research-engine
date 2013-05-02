# Here we hold and generatethe texts for emails. 
# Perhaps later this will be a little smarter...

from google.appengine.api import mail
from google.appengine.ext import db
from generic import *

ADMIN_EMAIL = "Research Engine <admin@research-engine.appspotmail.com>"


######################
##   Web Handlers   ##
######################

class SendNotifications(GenericPage):
    def get(self):
        logging.debug("CRON: Handler %s has been requested by cron" % self.__class__.__name__)
        for u in RegisteredUsers.query().iter():
            notifications_list = []
            for n in EmailNotifications.query(EmailNotifications.sent == False, ancestor = u.key).order(EmailNotifications.date).iter():
                notifications_list.append(n)
            send_notifications(notifications_list, u)
        self.write("Done")


##########################
##   Helper Functions   ##
##########################

def classify_notifications(notifications_list):
    notifs = {"WikiRevisions" : [], "NotebookNotes" : [], "NoteComments" : [], "WritingRevisions" : [], "CodeComments" : [], 
              "CodeRepositories" : [], "DataRevisions" : [],"ForumThreads" : [],"ForumComments" : []}            
    for n in notifications_list:
        notifs[str(n.category)].append(n)
    return notifs


def send_notifications(notifications_list, user):
    if len(notifications_list) == 0: return
    notifs = classify_notifications(notifications_list)
    message = mail.EmailMessage(sender = ADMIN_EMAIL,
                                to = user.email,
                                subject = "Recent activity in your projects.",
                                body = render_str("emails/notification_email.txt", **notifs),
                                html = render_str("emails/notification_email.html", **notifs))
    logging.debug("EMAIL: Sending an email with notifications to user %s" % user.username)
    message.send()
    for n in notifications_list:
        n.sent = True
        logging.debug("DB WRITE: CRON: Changing a notification's 'sent' property to True")
        n.put()
    return


def send_verify_email(user):
    link = "http://research-engine.appspot.com/verify_email?username=%s&h=%s" % (user.username, hash_str(user.username + user.salt))
    message = verify_email_message(link)
    message.to = user.email
    logging.debug("EMAIL: Sending an email verification request.")
    message.send()
    return


def send_invitation_to_project(project, inviting, invited):
    h = hash_str(inviting.username + invited.username + str(project.key))
    kw = {"project" : project,
          "inviting" : inviting,
          "invited" : invited,
          "DOMAIN_PREFIX" : DOMAIN_PREFIX,
          "accept_link" : "%s/%s/%s/admin?h=%s" % (DOMAIN_PREFIX, inviting.username, project.key.integer_id(), h)}
    message = mail.EmailMessage(sender = ADMIN_EMAIL,
                                to = invited.email,
                                subject = "%s has invited you to collaborate in the project %s" % (inviting.username.capitalize(), project.name),
                                body = render_str("emails/invite_to_project.txt" , **kw),
                                html = render_str("emails/invite_to_project.html", **kw))
    logging.debug("EMAIL: Sending an email with a invitation to a project from user %s to user %s" % (inviting.username, invited.username))
    message.send()
    return

###
### Beware!! Uglyness below! 
###

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
We received a request to create a new account on our website with this email address. If you made this request please visit the following link to confirm your email:<br/><br/>
<a href="%s">%s</a><br/><br/>
If you didn't made this request, please ignore this email.
""" % (verify_link, verify_link)
    html += SIGNATURE_HTML

    message = mail.EmailMessage(sender = ADMIN_EMAIL,
                                subject = "Email verification.",
                                body = body,
                                html = html)
    return message
        
