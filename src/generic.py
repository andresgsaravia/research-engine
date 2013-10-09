# generic.py
# Functions related to all pages.
# Every source page should import this.

import webapp2 
import jinja2
import os, re, string, hashlib, logging
from google.appengine.ext import ndb, db, blobstore
from google.appengine.ext.webapp import blobstore_handlers

import filters

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEBUG = True             # Debug messages using logging.debug
SALT_LENGTH = 16

jinja_env.filters['md'] = filters.md

# You should change these if you are registering your own app on App Engine
APP_NAME = "Research Engine"
APP_URL = "https://research-engine.appspot.com"
ADMIN_EMAIL = "admin@research-engine.appspotmail.com"
APP_REPO = "https://github.com/andresgsaravia/research-engine"

MAX_RECENT_ACTIVITY_ITEMS = 20

##########################
##   Helper Functions   ##
##########################

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

# Hashing
def make_salt(length = SALT_LENGTH):
    assert length > 0
    return ''.join(string.lowercase[ord(os.urandom(1)) % 26] for x in range(length))

def hash_str(s):
    return hashlib.sha256(s).hexdigest()

def make_secure_val(val, salt):
    return "%s|%s" % (val, hash_str(val + salt))

def get_secure_val(h, salt):
    val = h.split("|")[0]
    if h == make_secure_val(val, salt):
        return val
    return None



###########################
##   Datastore Objects   ##
###########################

# User related stuff.

class UnverifiedUsers(ndb.Model):
    username = ndb.StringProperty(required = True)
    email = ndb.StringProperty(required = True)
    salt = ndb.StringProperty(required = True)
    password_hash = ndb.TextProperty(required = True)


class RegisteredUsers(ndb.Model):
    username = ndb.StringProperty(required = True)
    password_hash = ndb.TextProperty(required = True)
    salt = ndb.StringProperty(required = True)
    email = ndb.StringProperty(required = False)
    about_me = ndb.TextProperty(required = False)
    my_projects = ndb.KeyProperty(repeated = True)                   # keys to Projects (defined in projects.py)
    profile_image_url = ndb.StringProperty(required = False)

    def list_of_projects(self):
        projects_list = []
        for p_key in self.my_projects:
            project = p_key.get()
            if project: 
                projects_list.append(project)
            else:
                logging.warning("RegisteredUser with key (%s) contains a broken reference to project %s" 
                                % (self.key, p_key))
        if len(projects_list) > 0:
            projects_list.sort(key=lambda p: p.last_updated, reverse=True)
        return projects_list

    def get_profile_image(self, size = 0):
        assert type(size) == int
        if not self.profile_image_url:
            self.profile_image_url = "https://secure.gravatar.com/avatar/" + hashlib.md5(self.email.strip().lower()).hexdigest()
            if DEBUG: logging.debug("DB WRITE: Updating a user's profile_image_url attribute")
            self.put()
        url = self.profile_image_url
        if size > 0: url += "?s=" + str(size)
        return url

    def get_recent_activity(self, include_seen_p = False, max_items = MAX_RECENT_ACTIVITY_ITEMS):
        if include_seen_p:
            return UserActivities.query(ancestor = self.key).order(-UserActivities.date).fetch(max_items)
        else:
            return UserActivities.query(UserActivities.seen_p == False, ancestor = self.key).order(-UserActivities.date).fetch(max_items)

# Each Notification should have as parent a RegisteredUser, this parent is the one who will receive the notification
class EmailNotifications(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers)
    category = ndb.StringProperty(required = True)
    html = ndb.TextProperty(required = True)
    txt = ndb.TextProperty(required = False)
    sent = ndb.BooleanProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)


# Each UserActivity should have a RegisteredUser as parent
class UserActivities(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add = True)
    kind = ndb.StringProperty(required = True)
    item = ndb.KeyProperty(required = True)
    seen_p = ndb.BooleanProperty(default = False) # Wether this activity has been seen by the parent RegisteredUser

    def description_html(self):
        html = ''
        if self.kind == "Projects":
            author = self.key.parent().get()
            item = self.item.get()
            html = '<a href="/%s">%s</a> ' % (author.username, author.username.capitalize())
            if item.__class__.__name__ == "Notebooks":
                html += "started a new notebook " 
                html += '<a href="/%s/notebooks/%s">%s</a>' % (item.key.parent().integer_id(), item.key.integer_id(), item.name)
            elif item.__class__.__name__ == "NotebookNotes":
                html += 'made a new note: <a href="/%s/notebooks/%s/%s">%s</a> ' % (item.key.parent().parent().integer_id(), 
                                                                                     item.key.parent().integer_id(), item.key.integer_id(),
                                                                                     item.title)
                html += 'in the notebook '
                html += '<a href=/%s/notebooks/%s>%s</a>' % (item.key.parent().parent().integer_id(), item.key.parent().integer_id(), item.key.parent().get().name)
        return html


######################
##   Web Handlers   ##
######################

class GenericPage(webapp2.RequestHandler):

    # Querying the Datastore
    def log_read(self, dbmodel, message = ''):
        if DEBUG: logging.debug("DB READ: Handler %s requests an instance of %s. %s"
                                % (self.__class__.__name__, dbmodel.__name__, message))
        return
    
    # Writing the Datastore
    def log_and_put(self, instance, message = ''):
        if DEBUG: logging.debug("DB WRITE: Handler %s is writing an instance of %s. %s"
                                % (self.__class__.__name__, instance.__class__.__name__, message))
        instance.put()
        return

    def log_and_delete(self, instance, message = ''):
        if DEBUG: logging.debug("DB WRITE: Handler %s is deleting an instance of %s. %s"
                      % (self.__class__.__name__, instance.__class__.__name__, message))
        instance.key.delete()
        return

    def add_notifications(self, category, author, users_to_notify, html, txt):
        for u in users_to_notify:
            notification = EmailNotifications(author = author, category = category, html = html, txt = txt,
                                              sent = False, parent = u.key)
            self.log_and_put(notification)
        return


    # Cookies
    def get_cookie_val(self, cookie_name, salt):
        cookie = self.request.cookies.get(cookie_name)
        if cookie:
            val = get_secure_val(cookie, salt)
            return val
        return None

    def set_cookie(self, name, value, salt, path = "/", max_age = None):
        cookie = "%s=%s; Path=%s; " % (name, make_secure_val(value, salt), path)
        if max_age: cookie += "max-age=%s" % max_age
        self.response.headers.add_header('Set-Cookie', str(cookie))
        return

    def remove_cookie(self, name, path = "/"):
        cookie = self.request.cookies.get(name)
        if cookie:
            del_cookie = "%s=; Path=%s" % (name, path)
            self.response.headers.add_header('Set-Cookie', str(del_cookie))
            return True
        return False

    # Users
    def get_login_user(self):
        cookie = self.request.cookies.get("username")
        if not cookie: return None
        cookie_username = cookie.split("|")[0]
        self.log_read(RegisteredUsers, "Getting logged in user. ")
        u = RegisteredUsers.query(RegisteredUsers.username == cookie_username).get()
        if not u: return None
        if not get_secure_val(cookie, u.salt): return None
        return u

    def get_user_by_username(self, username, log_message = ''):
        self.log_read(RegisteredUsers, log_message)
        return RegisteredUsers.query(RegisteredUsers.username == username).get()

    def get_user_by_email(self, email, log_message = ''):
        self.log_read(RegisteredUsers, log_message)
        return RegisteredUsers.query(RegisteredUsers.email == email).get()

    # Rendering
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        kw["APP_NAME"] = APP_NAME
        kw["APP_URL"] = APP_URL
        kw["APP_REPO"] = APP_REPO
        kw['user'] = self.get_login_user()
        self.write(self.render_str(template, **kw))


class GenericBlobstoreUpload(blobstore_handlers.BlobstoreUploadHandler):
    # Querying the Datastore
    def log_read(self, dbmodel, message = ''):
        if DEBUG: logging.debug("DB READ: Handler %s requests an instance of %s. %s"
                                % (self.__class__.__name__, dbmodel.__name__, message))
        return

    # Writing to the Datastore
    def log_and_put(self, instance, message = ''):
        if DEBUG: logging.debug("DB WRITE: Handler %s is writing an instance of %s. %s"
                                % (self.__class__.__name__, instance.__class__.__name__, message))
        instance.put()
        return

    def log_and_delete(self, instance, message = ''):
        if DEBUG: logging.debug("DB WRITE: Handler %s is deleting an instance of %s. %s"
                                % (self.__class__.__name__, instance.__class__.__name__, message))
        instance.key.delete()
        return

    def add_notifications(self, category, author, users_to_notify, html, txt):
        for u in users_to_notify:
            notification = EmailNotifications(author = author.key, category = category, html = html, txt = txt,
                                              sent = False, parent = u)
            self.log_and_put(notification)
        return

    # Users
    def get_login_user(self):
        cookie = self.request.cookies.get("username")
        if not cookie: return None
        cookie_username = cookie.split("|")[0]
        self.log_read(RegisteredUsers, "Getting logged in user. ")
        u = RegisteredUsers.query(RegisteredUsers.username == cookie_username).get()
        if not u: return None
        if not get_secure_val(cookie, u.salt): return None
        return u

    def get_user_by_username(self, username, log_message = ''):
        self.log_read(RegisteredUsers, log_message)
        return RegisteredUsers.query(RegisteredUsers.username == username).get()
