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
        params["error"] = ''
        # Valid input
        logging.debug("DB READ: Checking if username is available for a new user.")
        logging.debug("DB READ: Checking if email is available for a new user.")
        if not re.match(USERNAME_RE, usern):
            params['error_username'] = "*"
            params['error'] += "That's not a valid username. "
            have_error = True
        elif db.GqlQuery("select * from RegisteredUsers where username = '%s'" % usern).get():
            params['error_username'] = "*"
            params['error'] += 'That username is not available.'
            have_error = True
        elif db.GqlQuery("select * from RegisteredUsers where email = '%s'" % email).get():
            params['error_email'] = "*"
            params['error'] += 'That email is already in use by someone. Did you <a href="/recover_password">forget your password?. </a>'
            have_error = True
        if not re.match(PASSWORD_RE, password):
            params['error_password'] = "*"
            params['error'] += "That's not a valid password. "
            have_error = True
        elif password != verify:
            params['error_verify'] = "*"
            params['error'] += "Your passwords didn't match. "
            have_error = True
        if not re.match(EMAIL_RE, email):
            params['error_email'] = "*"
            params['error'] += "That doesn't seem like a valid email. "
            have_error = True
        # Render
        if have_error:
            self.render('signup.html', **params)
        else:
            salt = make_salt()
            ph = hash_str(password + salt)
            u = RegisteredUsers(username = usern, password_hash = ph, salt = salt, email = email)
            logging.debug("DB WRITE: New user registration.")
            u.put()
            self.set_cookie("username", usern, salt)
            self.redirect('/')

class LoginPage(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("login.html", username = username)

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        have_error = False
        params = {'email' : email, 'password' : password, 'error' : ''}
        if not email:
            params["error"] += "You must provide a valid email. "
            have_error = True
        if not password:
            params["error"] += "You must provide your password. "
            have_error = True
        if not have_error:
            logging.debug("DB READ: Finding user to login.")
            u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE email = :1", email).get()
            if (not u) or (u.password_hash != hash_str(password + u.salt)):
                params["error"] = 'Invalid password. If you forgot your password you can recover it <a href="/recover_password">here.</a>'
                have_error = True
        if have_error:
            self.render("login.html", **params)
        else:
            self.set_cookie("username", u.username, u.salt)
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
        params["contacts"] = []
        for contact_key in user.contacts:
            params["contacts"].append(self.get_item_from_key(contact_key))
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
        params["info"] = ''
        params["error"] = ''
        have_error = False
        if user.username != params["usern"]:
            # Check if new username is available
            logging.debug("DB READ: Checking availability to change a username.")
            u2 = RegisteredUsers.all().filter("username =", params["usern"]).get()
            if u2 or (not re.match(USERNAME_RE, params["usern"])):
                params["error_username"] = "*"
                params['error'] += "Sorry, that username is not available. "
                have_error = True
        if user.email != params["email"]:
            logging.debug("DB READ: Checking availability to change an email.")
            u2 = RegisteredUsers.all().filter("email =", params["email"]).get()
            if u2:
                params["error_email"] = "*"
                params["error"] += "That email is already in use by someone. "
                have_error = True
        if not re.match(EMAIL_RE, params["email"]):
                params["error_email"] = "*"
                params["error"] += "That doesn't seem like a valid email. "
                have_error = True
        if have_error:
            self.render("settings.html", **params)
        else:
            user.username = params["usern"] 
            user.email = params["email"]
            user.about_me = params["about_me"]
            logging.debug("DB WRITE: Updating user's settings.")
            user.put()
            params["info"] = "Changes saved"
            self.set_cookie("username", user.username, user.salt)
            self.render("settings.html", **params)


class UserPage(GenericPage):
    def get(self, page_user_key):
        logged_in_user = self.get_user()
        page_user = self.get_item_from_key_str(page_user_key)
        params = {"logged_in_user" : logged_in_user, "page_user" : page_user}
        if not page_user:
            self.error(404)
            return
        if logged_in_user.key() == page_user.key():
            self.redirect("/settings")
            return
        if page_user.key() in logged_in_user.contacts:
            params["is_contact_message"] = '%s is in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            params["button_message"] = "Remove from contacts"
        else:
            params["is_contact_message"] = '%s is not in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            params["button_message"] = "Add to contacts"
        self.render("user.html", **params)
            
    def post(self, page_user_key):
        logged_in_user = self.get_user()
        if not logged_in_user:
            self.redirect("/login")
            return
        page_user = self.get_item_from_key_str(page_user_key)
        if not page_user:
            self.error(404)
            return
        params ={"logged_in_user" : logged_in_user, "page_user" : page_user}
        if page_user.key() in logged_in_user.contacts:
            logged_in_user.contacts.remove(page_user.key())
            logging.debug("DB WRITE: Handler UserPage is removing a contact from a user's contacts list.")
            logged_in_user.put()
            params["is_contact_message"] = '%s is not in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            params["info_message"] = "Contact removed from your contacts list."
            params["button_message"] = "Add to contacts"
        else:
            logged_in_user.contacts.append(page_user.key())
            logging.debug("DB WRITE: Handler UserPage is adding a contact from a user's contacts list.")
            logged_in_user.put()
            params["is_contact_message"] = '%s is in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            params["info_message"] = "Contact added to your contacts list."
            params["button_message"] = "Remove from contacts"
        self.render("user.html", **params)


class SearchForUserPage(GenericPage):
    def get(self):
        self.render("search_for_user.html")

    def post(self):
        search_username = self.request.get("search_username")
        have_error = False
        error = ''
        if not search_username:
            have_error = True
            error += 'You must provide an username to search for.'
        logging.debug("DB READ: Handler SearchForUserPage is searching for an user using its username. ")
        u = RegisteredUsers.all().filter("username =", search_username).get()
        if search_username and (not u):
            have_error = True
            error += "Sorry, we don't know any user with that username."
        if have_error:
            self.render("search_for_user.html", error = error, search_username = search_username)
        else:
            self.redirect("/user/%s" % u.key())


class ContactsPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        contacts = []
        for contact_key in user.contacts:
            contacts.append(self.get_item_from_key(contact_key))
        self.render("contacts.html", contacts = contacts)
