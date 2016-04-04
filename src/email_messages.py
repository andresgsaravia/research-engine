# Here we hold and generatethe texts for emails. 
# Perhaps later this will be a little smarter...

from google.appengine.api import mail
from google.appengine.ext import ndb
import logging
import generic

PRETTY_ADMIN_EMAIL = generic.APP_NAME + " <" + generic.ADMIN_EMAIL + ">"


###########################
##   Datastore Objects   ##
###########################

class EmailsToSend(ndb.Model):
    sender  = ndb.StringProperty(default = PRETTY_ADMIN_EMAIL)
    to      = ndb.StringProperty(required = True)
    subject = ndb.StringProperty(required = True)
    body    = ndb.TextProperty(required = True)
    html    = ndb.TextProperty(default = "") 


######################
##   Web Handlers   ##
######################

class SendPendingEmails(generic.GenericPage):
    def get(self):
        emails = EmailsToSend.query().fetch()
        for email in emails:
            em = mail.EmailMessage(sender  = email.sender,
                                   to      = email.to,
                                   subject = email.subject,
                                   body    = email.body,
                                   html    = email.html)
            logging.debug("EMAIL: Sending a pending email to %s" % email.to)
            em.send()
            email.key.delete()


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
    message = mail.EmailMessage(sender = PRETTY_ADMIN_EMAIL,
                                to = user.email,
                                subject = "Recent activity in your projects",
                                body = generic.render_str("emails/notification_email.txt", **notifs),
                                html = generic.render_str("emails/notification_email.html", **notifs))
    logging.debug("EMAIL: Sending an email with notifications to user %s" % user.username)
    message.send()
    for n in notifications_list:
        n.sent = True
        logging.debug("DB WRITE: CRON: Changing a notification's 'sent' property to True")
        n.put()
    return


def send_verify_email(user):
    link = "%s/verify_email?username=%s&h=%s" % (generic.APP_URL, user.username, generic.hash_str(user.username + user.salt))
    message = verify_email_message(link)
    message.to = user.email
    logging.debug("EMAIL: Sending an email verification request.")
    message.send()
    return


def send_invitation_to_project(project, inviting, invited, message):
    h = generic.hash_str(invited.salt + str(project.key))
    kw = {"project" : project,
          "inviting" : inviting,
          "invited" : invited,
          "message" : message,
          "APP_URL" : generic.APP_URL,
          "accept_link" : "%s/%s/admin?h=%s" % (generic.APP_URL, project.key.integer_id(), h)}
    message = mail.EmailMessage(sender = PRETTY_ADMIN_EMAIL,
                                to = invited.email,
                                subject = "%s has invited you to collaborate in the project %s" % (inviting.username.capitalize(), project.name),
                                body = generic.render_str("emails/invite_to_project.txt" , **kw),
                                html = generic.render_str("emails/invite_to_project.html", **kw))
    logging.debug("EMAIL: Sending an email with a invitation to a project from user %s to user %s" % (inviting.username, invited.username))
    message.send()
    return

def send_invitation_to_group(group, inviting, invited):
    h = generic.hash_str(invited.salt + str(group.key))
    kw = {"group" : group,
          "inviting" : inviting,
          "invited" : invited,
          "APP_URL" : generic.APP_URL,
          "accept_link" : "%s/g/%s/invited?h=%s" % (generic.APP_URL, group.key.integer_id(), h)}
    message = mail.EmailMessage(sender = PRETTY_ADMIN_EMAIL,
                                to = invited.email,
                                subject = "%s has invited you to be a member of the group %s" % (inviting.username.capitalize(), group.name),
                                body = generic.render_str("emails/invite_to_group.txt" , **kw),
                                html = generic.render_str("emails/invite_to_group.html", **kw))
    logging.debug("EMAIL: Sending an email with a invitation to a group from user %s to user %s" % (inviting.username, invited.username))
    message.send()
    return

def send_new_calendar_event_notification(user, author, group, event, update):
    kw = {"user"    : user,
          "author"  : author,
          "group"   : group,
          "event"   : event,
          "APP_URL" : generic.APP_URL,
          "update"  : update,
          "subject" : "An event has changed in your group " if update else "New event in your group "}
    kw["subject"] = kw["subject"] + group.name
    message = EmailsToSend(sender  = PRETTY_ADMIN_EMAIL,
                           to      = user.email,
                           subject = kw["subject"],
                           body    = generic.render_str("emails/group_event_notification.txt", **kw),
                           html    = generic.render_str("emails/group_event_notification.html", **kw))
    message.put()
    return


def send_group_biblio_notification(group, user, bibitems):
    kw = {"group"    : group,
          "user"     : user,
          "bibitems" : bibitems,
          "APP_URL"  : generic.APP_URL}
    message = mail.EmailMessage(sender  = PRETTY_ADMIN_EMAIL,
                                to      = user.email,
                                subject = "Weekly bibliography review for %s" % group.name,
                                body    = generic.render_str("emails/group_biblio_notification.txt", **kw),
                                html    = generic.render_str("emails/group_biblio_notification.html", **kw))
    logging.debug("EMAIL: Sending an email with an event notification to user %s" % user.username)
    message.send()
    return

###
### Beware!! Uglyness below! 
###

SIGNATURE = """
-----------------------------------
%s <%s>""" % (generic.APP_NAME, generic.APP_URL)


SIGNATURE_HTML = """<br/>
-----------------------------------<br/>
<a href="%s">%s</a>""" % (generic.APP_URL, generic.APP_NAME)


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

    message = mail.EmailMessage(sender = PRETTY_ADMIN_EMAIL,
                                subject = "Email verification",
                                body = body,
                                html = html)
    return message
        
