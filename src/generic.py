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
DOMAIN_PREFIX = "http://research-engine.appspot.com"

jinja_env.filters['md'] = filters.md


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

    def list_of_projects(self):
        projects_list = []
        for p_key in self.my_projects:
            project = p_key.get()
            if project: 
                projects_list.append(project)
            else:
                logging.warning("RegisteredUser with key (%s) contains a broken reference to project %s" 
                                % (self.key(), p_key))
        if len(projects_list) > 0:
            projects_list.sort(key=lambda p: p.last_updated, reverse=True)
        return projects_list


# Each Notification should have as parent a RegisteredUser, this parent is the one who will receive the notification
class EmailNotifications(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers)
    category = ndb.StringProperty(required = True)
    html = ndb.TextProperty(required = True)
    txt = ndb.TextProperty(required = False)
    sent = ndb.BooleanProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)


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

    def get_user_by_email(self, email, logmessage = ''):
        self.log_read(RegisteredUsers, log_message)
        return RegisteredUsers.query(RegisteredUsers.email == email).get()

    # Rendering
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        kw['user'] = self.get_login_user()
        if kw['user'] is None:
            kw['login_message'] = ('<a href="/login">Login</a> <ul><li><a href="/signup">Signup</a></li></ul>')
        else:
            kw['login_message'] = ('<a href="/%s">%s</a> <ul><li><a href="/settings">Settings</a></li><li><a href="/logout">Logout</a></li></ul>' 
                                   % (kw['user'].username, kw['user'].username.title()))            
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
