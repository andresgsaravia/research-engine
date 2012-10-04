# generic.py
# Functions related to all pages.
# Every source page should import this.

import webapp2 
import jinja2
import os, re, string, hashlib, logging
from google.appengine.ext import db
from google.appengine.api import users

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

SALT_LENGTH = 16

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


# User related stuff.

class RegisteredUsers(db.Model):
    username = db.StringProperty(required = True)
    password_hash = db.TextProperty(required = True)
    salt = db.StringProperty(required = True)
    email = db.EmailProperty(required = False)
    about_me = db.TextProperty(required = False)
    google_userid = db.StringProperty(required = False)


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


# Handlers.

class GenericPage(webapp2.RequestHandler):

    # Cookies
    def get_cookie_val(self, cookie_name, salt):
        cookie = self.request.cookies.get(cookie_name)
        if cookie:
            val = get_secure_val(cookie, salt)
            return val
        return None

    def get_username(self):
        cookie = self.request.cookies.get("username")
        if not cookie:
            return None
        cookie_username = cookie.split("|")[0]
        logging.debug("DB READ: Checking if user exists and retriving its validated username.")
        u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE username = :1", cookie_username).get()
        if not u:
            return None
        return get_secure_val(cookie, u.salt)

    def set_cookie(self, name, value, salt, path = "/"):
        cookie = "%s=%s; Path=%s" % (name, make_secure_val(value, salt), path)
        self.response.headers.add_header('Set-Cookie', str(cookie))
        return

    def remove_cookie(self, name, path = "/"):
        cookie = self.request.cookies.get(name)
        if cookie:
            del_cookie = "%s=; Path=%s" % (name, path)
            self.response.headers.add_header('Set-Cookie', str(del_cookie))
            return True
        return False
    
    # Rendering related stuff.    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        kw['username'] = self.get_username()
        if kw['username'] is None:
            kw['login_message'] = ('You are not logged in. <a title="If you are an existing user, click here." href="/login">Login</a> or <a title="If you are a new user, click here." href="/signup">Signup</a>')
        else:
            kw['login_message'] = ('You are signed in as <a title="Click here to edit your settings." href="/settings">%s</a>. <a href="/logout">Logout</a>' % 
                                   kw['username'])            
        self.write(self.render_str(template, **kw))
