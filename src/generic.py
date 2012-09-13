# generic.py
# Functions related to all pages.
# Every source page should import this.

import webapp2 
import jinja2
import os, re, string, hashlib
from google.appengine.ext import db
from google.appengine.api import users

template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


# User related stuff.

class RegisteredUsers(db.Model):
    userid = db.StringProperty(required = True)
    email = db.EmailProperty(required = True)
    username = db.StringProperty(required = True)
    about_me = db.TextProperty(required = False)


# Handlers.

class GenericPage(webapp2.RequestHandler):

    # Database queries.
    def get_user_data(self, user):
        return db.GqlQuery("SELECT * FROM RegisteredUsers WHERE userid = :1", user.user_id()).get()

    def get_username(self, user):
        if not user:
            return "Anonymous"
        u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE userid = :1", user.user_id()).get()
        if u:
            return u.username
        else:
            return None

    # Rendering related stuff.    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        user = users.get_current_user()
        if user:
            kw['username'] = self.get_username(user)
            kw['login_message'] = ('You are signed in as %s. <a href="/logout">Logout</a>' % 
                                   kw['username'])            
        else:
            kw['login_message'] = ('You are not logged in. <a href="/login">Login</a>')
            kw['username'] = 'Anonymous user'
        self.write(self.render_str(template, **kw))
