# users.py
# All related to user login/signup and preferences storage.

from generic import *

EMAIL_RE = r'^[\S]+@[\S]+\.[\S]+$'
USERNAME_RE = r'^[a-zA-Z0-9_-]{3,20}$'

class NewUserPage(GenericPage):
    def get(self):
        user = users.get_current_user()
        # Not logged in.
        if not user:
            self.redirect("/")
            return
        # Check if user is already in database.
        u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE userid = :1", user.user_id()).get()
        if u is None:
            u = RegisteredUsers(userid = user.user_id(), email = user.email(), username = user.nickname())
            u.put()
            self.render("new_user.html")
        else:
            self.redirect("/settings")


class LoginPage(GenericPage):
    def get(self):
        user = users.get_current_user()
        params = dict(user = user)
        if user:
            params['username'] = self.get_user_data(user).username
            params['logout_url'] = users.create_logout_url("/login")
        else:
            params['login_url'] = users.create_login_url("/new_user")
        self.render("login.html", **params)

            
class LogoutPage(GenericPage):
    def get(self):
        self.redirect("%s" % users.create_logout_url("/login"))


class SettingsPage(GenericPage):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/login")
            return
        user_data = self.get_user_data(user)
        self.render("settings.html", email = user_data.email, about_me = user_data.about_me)

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/login")
            return
        username = self.request.get('username')
        email = self.request.get('email')
        about_me = self.request.get('about_me')
        have_error = False
        params = dict(username = username, email = email, about_me = about_me)

        # Valid input?
        if not re.match(EMAIL_RE, email):
            params['error_email'] = "That doesn't seem like a valid email address."
            have_error = True
        if not re.match(USERNAME_RE, username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if have_error:
            self.render('settings.html', **params)
        else:
            u_data = self.get_user_data(user)
            u_data.username = username
            u_data.email = email
            u_data.about_me = about_me
            u_data.put()
            params['username'] = username
            params['email'] = email
            params['about_me'] = about_me
            params['bottom_message'] = 'Changes successfully applied.'
            self.render('settings.html', **params)

