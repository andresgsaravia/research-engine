# generic.py
# Functions related to all pages.
# Every source page should import this.

import webapp2
import jinja2
import os, re, string, hashlib, logging, datetime, json
from google.appengine.ext import ndb, db, blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch
from webapp2_extras import auth, sessions

import filters, secrets

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEBUG = True             # Debug messages using logging.debug
SALT_LENGTH = 16

jinja_env.filters['md'] = filters.md

# You should change these if you are registering your own app on App Engine
APP_NAME = "Research Engine"
APP_VERSION = "1.4.0"
APP_URL = "https://research-engine.appspot.com"
ADMIN_EMAIL = "admin@research-engine.appspotmail.com"
APP_REPO = "https://github.com/andresgsaravia/research-engine"
GOOGLE_PLUS_PAGE = "https://plus.google.com/+ResearchEngineAppspotApp"

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
    gplusid = ndb.StringProperty(required = False)
    gplus_profile_json = ndb.JsonProperty(required = False)

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

    def set_gplus_profile(self):
        assert self.gplusid
        try:
            p = json.loads(urlfetch.fetch("https://www.googleapis.com/plus/v1/people/%s?key=%s" % (self.gplusid, secrets.GOOGLE_PLUS_KEY)).content)
            self.gplus_profile_json = p
            self.put()
        except:
            logging.warning("There was an error getting and/or parsing a user's G+ profile")

    def set_profile_image_url(self, provider = "gravatar"):
        assert provider in ["gravatar","google"]
        if provider == "gravatar":
            self.profile_image_url = "https://secure.gravatar.com/avatar/" + hashlib.md5(self.email.strip().lower()).hexdigest()
        elif provider == "google":
            assert self.gplus_profile_json
            self.profile_image_url = self.gplus_profile_json['image']['url'].split('?')[0]
        if DEBUG: logging.debug("DB WRITE: Updating a user's profile_image_url attribute")
        self.put()
        return

    def get_profile_image(self, size = 0):
        assert type(size) == int
        assert self.profile_image_url
        url = self.profile_image_url
        if size > 0:
            url += "?sz=" if self.gplus_profile_json else "?s="
            url += str(size)
        return url

    def get_recent_activity(self, days = 7):
        project_actvs = UserActivities.query(UserActivities.actv_kind == "Projects",
                                             UserActivities.date > (datetime.datetime.now() - datetime.timedelta(days=days)),
                                             ancestor = self.key).order(-UserActivities.date).fetch()
        r = {"Projects" : project_actvs}
        return r

    def get_project_contributions_counts(self, days, self_user_p):
        actvs = UserActivities.query(UserActivities.actv_kind == "Projects",
                                             UserActivities.date > (datetime.datetime.now() - datetime.timedelta(days=days)),
                                             ancestor = self.key).fetch()
        counts = {}
        for a in actvs:
            if self_user_p or a.is_open_p():
                if a.relative_to in counts:
                    counts[a.relative_to] += 1
                else:
                    counts[a.relative_to] = 1
        return counts


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
    actv_kind = ndb.StringProperty(required = True)  # Wether is a "Project" update or, in the future, something else
    relative_to = ndb.KeyProperty(required = True) # For now this is only the project the activity is related to. In the future might be something else
    item = ndb.KeyProperty(required = True)

    def description_html(self, hide_username_p = False, show_project_p = True):
        html = ''
        relative_to = self.relative_to.get()
        author = self.key.parent().get()
        if relative_to.__class__.__name__ == "Projects":
            html = render_str("project_activity.html", author = author, item = self.item, project = relative_to,
                              hide_username_p = hide_username_p, show_project_p = show_project_p)
        return html

    def is_open_p(self):
        try:
            val = self.item.get().is_open_p()
        except:
            val = False
        return val


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
        kw["APP_VERSION"] = APP_VERSION
        kw["APP_URL"] = APP_URL
        kw["APP_REPO"] = APP_REPO
        kw["GOOGLE_PLUS_PAGE"] = GOOGLE_PLUS_PAGE
        kw['user'] = self.get_login_user()
        if kw["user"]: kw["list_of_projects"] = kw["user"].list_of_projects()
        self.write(self.render_str(template, **kw))

    # for simpleauth
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)


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


class RenderPreview(GenericPage):
    def post(self):
        content = self.request.get("content")
        wiki_p_id = self.request.get("wiki_p_id")
        self.write(filters.md(content, wiki_p_id))
