# users.py
# All related to user login/signup and preferences storage.

from generic import *

EMAIL_RE = r'^[\S]+@[\S]+\.[\S]+$'
USERNAME_RE = r'^[a-zA-Z0-9_-]{3,20}$'
PASSWORD_RE = r'^.{3,20}$'

class SignupPage(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("signup.html", username = username)

    def post(self):
        usern = self.request.get('usern')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        have_error = False
        params = {}
        params["usern"] = usern 
        params["email"] = email
        params["error_message"] = ''
        # Valid input
        logging.debug("DB READ: Checking if username is available.")
        if not re.match(USERNAME_RE, usern):
            params['error_username'] = "*"
            params['error_message'] += "That's not a valid username. "
            have_error = True
        elif db.GqlQuery("select * from RegisteredUsers where username = '%s'" % usern).get():
            params['error_username'] = "*"
            params['error_message'] += "That username is not available. "
            have_error = True
        if not re.match(PASSWORD_RE, password):
            params['error_password'] = "*"
            params['error_message'] += "That's not a valid password. "
            have_error = True
        elif password != verify:
            params['error_verify'] = "*"
            params['error_message'] += "Your passwords didn't match. "
            have_error = True
        if not re.match(EMAIL_RE, email):
            params['error_email'] = "*"
            params['error_message'] += "That doesn't seem like a valid email. "
            have_error = True
        # Render
        if have_error:
            self.render('signup.html', **params)
        else:
            salt = make_salt()
            ph = hash_str(password + salt)
            u = RegisteredUsers(username = usern, password_hash = ph, salt = salt)
            if email: u.email = email
            logging.debug("DB WRITE: New user registration.")
            u.put()
            self.set_cookie("username", usern, salt)
            self.redirect('/')

class LoginPage(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("login.html", username = username)

    def post(self):
        usern =self.request.get('usern')
        password = self.request.get('password')
        have_error = False
        params = dict(usern = usern, password = password)
        if not usern:
            params["error_username"] = "You must provide a valid username."
            have_error = True
        if not password:
            params["error_password"] = "You must provide your password."
            have_error = True
        if not have_error:
            logging.debug("DB READ: Finding user to login.")
            u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE username = :1", usern).get()
            if (not u) or (u.password_hash != hash_str(password + u.salt)):
                params["error_password"] = "Invalid password"
                have_error = True
        if have_error:
            self.render("login.html", **params)
        else:
            self.set_cookie("username", usern, u.salt)
            self.redirect("/")            


class LogoutPage(GenericPage):
    def get(self):
        self.remove_cookie("username")
        self.redirect("/login")


class SettingsPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        params = {}
        params["usern"] = user.username
        if user.email: params["email"] = user.email
        if user.about_me: params["about_me"] = user.about_me
        self.render("settings.html", **params)

    def post(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        params = {}
        params["usern"] = self.request.get("usern")
        params["email"] = self.request.get("email")
        params["about_me"] = self.request.get("about_me")
        params["bottom_message"] = ''
        have_error = False
        u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE username = :1", user.username).get()
        if user.username != params["usern"]:
            # Check if available
            logging.debug("DB READ: Checking availability to change a username.")
            u2 = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE username = :1", params["usern"]).get()
            if u2 or (not re.match(USERNAME_RE, params["usern"])):
                params["error_username"] = "*"
                params['bottom_message'] += "Sorry, that username is not available. "
                have_error = True
        if not re.match(EMAIL_RE, params["email"]):
                params["error_email"] = "*"
                params["bottom_message"] += "That doesn't seem like a valid email. "
                have_error = True
        if have_error:
            params["bottom_message"] = '<div class="error">%s</div>' % params["bottom_message"]
            self.render("settings.html", **params)
        else:
            u.username = params["usern"] 
            u.email = params["email"]
            u.about_me = params["about_me"]
            logging.debug("DB WRITE: Updating user's settings.")
            u.put()
            params["bottom_message"] = "Changes saved"
            self.render("settings.html", **params)
