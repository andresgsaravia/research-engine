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
        kw = {"usern" : usern, "email" : email, "error" : ''}
        # Valid input
        logging.debug("DB READ: Checking if username is available for a new user.")
        logging.debug("DB READ: Checking if email is available for a new user.")
        if not re.match(USERNAME_RE, usern):
            kw['error_username'] = "*"
            kw['error'] += "That's not a valid username. "
            have_error = True
        elif db.GqlQuery("select * from RegisteredUsers where username = '%s'" % usern).get():
            kw['error_username'] = "*"
            kw['error'] += 'That username is not available.'
            have_error = True
        elif db.GqlQuery("select * from RegisteredUsers where email = '%s'" % email).get():
            kw['error_email'] = "*"
            kw['error'] += 'That email is already in use by someone. Did you <a href="/recover_password">forget your password?. </a>'
            have_error = True
        if not re.match(PASSWORD_RE, password):
            kw['error_password'] = "*"
            kw['error'] += "That's not a valid password. "
            have_error = True
        elif password != verify:
            kw['error_verify'] = "*"
            kw['error'] += "Your passwords didn't match. "
            have_error = True
        if not re.match(EMAIL_RE, email):
            kw['error_email'] = "*"
            kw['error'] += "That doesn't seem like a valid email. "
            have_error = True
        # Render
        if have_error:
            self.render('signup.html', **kw)
        else:
            salt = make_salt()
            ph = hash_str(password + salt)
            u = RegisteredUsers(username = usern, password_hash = ph, salt = salt, email = email)
            self.log_and_put(u, "New user registration")
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
        kw = {'email' : email, 'password' : password, 'error' : ''}
        if not email:
            kw["error"] += "You must provide a valid email. "
            have_error = True
        if not password:
            kw["error"] += "You must provide your password. "
            have_error = True
        if not have_error:
            self.log_read(RegisteredUsers, "Checking user's login information.")
            u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE email = :1", email).get()
            if (not u) or (u.password_hash != hash_str(password + u.salt)):
                kw["error"] = 'Invalid password. If you forgot your password you can recover it <a href="/recover_password">here.</a>'
                have_error = True
        if have_error:
            self.render("login.html", **kw)
        else:
            u.salt = make_salt()
            u.password_hash = hash_str(password + u.salt)
            self.log_and_put(u, "Making new salt. ")
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
        kw = {"usern": user.username, "email" : user.email}
        if user.about_me: kw["about_me"] = user.about_me
        self.render("settings.html", **kw)


    def post(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        kw = {"usern"    : self.request.get("usern"),
              "email"    : self.request.get("email"),
              "about_me" : self.request.get("about_me"),
              "info"     : '',
              "error"    : ''}
        have_error = False
        if user.username != kw["usern"]:
            self.log_read(RegisteredUsers, "Checking if new username is available. ")
            u2 = RegisteredUsers.all().filter("username =", kw["usern"]).get()
            if u2 or (not re.match(USERNAME_RE, kw["usern"])):
                kw["error_username"] = "*"
                kw['error'] += "Sorry, that username is not available. "
                have_error = True
        if user.email != kw["email"]:
            self.log_read(RegisteredUsers, "Checking if new email is available. ")
            u2 = RegisteredUsers.all().filter("email =", kw["email"]).get()
            if u2:
                kw["error_email"] = "*"
                kw["error"] += "That email is already in use by someone. "
                have_error = True
        if not re.match(EMAIL_RE, kw["email"]):
                kw["error_email"] = "*"
                kw["error"] += "That doesn't seem like a valid email. "
                have_error = True
        if have_error:
            self.render("settings.html", **kw)
        else:
            user.username = kw["usern"] 
            user.email = kw["email"]
            user.about_me = kw["about_me"]
            self.log_and_put(user, "Updating settings.")
            kw["info"] = "Changes saved"
            self.set_cookie("username", user.username, user.salt)
            self.render("settings.html", **kw)


class UserPage(GenericPage):
    def get(self, page_user_key):
        logged_in_user = self.get_user()
        page_user = self.get_item_from_key_str(page_user_key, "Getting user instance of this page.")
        kw = {"logged_in_user" : logged_in_user, "page_user" : page_user}
        if not page_user:
            self.error(404)
            return
        if logged_in_user.key() == page_user.key():
            self.redirect("/settings")
            return
        if page_user.key() in logged_in_user.contacts:
            kw["is_contact"] = True
            kw["is_contact_message"] = '%s is in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            kw["button_message"] = "Remove from contacts"
            kw["projects_not_collaborating"] = []
            kw["projects_collaborating"] = []
            for project_key in logged_in_user.my_projects:
                project = self.get_item_from_key(project_key, "Logged in user's projects. ")
                if page_user.key() in project.authors:
                    kw["projects_collaborating"].append(project)
                else:
                    kw["projects_not_collaborating"].append(project)
        else:
            kw["is_contact"] = False
            kw["is_contact_message"] = '%s is not in <a href="/user/contacts">your contacts</a> list.' % page_user.username
            kw["button_message"] = "Add to contacts"
        self.render("user.html", **kw)
            
    def post(self, page_user_key):
        logged_in_user = self.get_user()
        if not logged_in_user:
            self.redirect("/login")
            return
        page_user = self.get_item_from_key_str(page_user_key, "Getting user instance of this page. ")
        if not page_user:
            self.error(404)
            return
        if page_user.key() in logged_in_user.contacts:
            logged_in_user.contacts.remove(page_user.key())
            self.log_and_put(logged_in_user, "Removing a contact.")
        else:
            logged_in_user.contacts.append(page_user.key())
            self.log_and_put(logged_in_user, "Adding a contact.")
        self.redirect("/user/%s" % page_user_key)


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
