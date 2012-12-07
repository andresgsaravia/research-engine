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
        if not re.match(USERNAME_RE, usern):
            kw['error_username'] = "*"
            kw['error'] += "That's not a valid username, it must be from 3 to 20 characters long and contain only letters, numbers, dashes and underscores. "
            have_error = True
        if not re.match(EMAIL_RE, email):
            kw['error_email'] = "*"
            kw['error'] += "That doesn't seem like a valid email. "
            have_error = True
        if not re.match(PASSWORD_RE, password):
            kw['error_password'] = "*"
            kw['error'] += "That's not a valid password, it must be between 3 and 20 characters long. "
            have_error = True
        elif password != verify:
            kw['error_verify'] = "*"
            kw['error'] += "Your passwords didn't match. "
            have_error = True
        if not have_error:
            # Available username
            self.log_read(RegisteredUsers, "Checking if username is available. ")
            another_user = RegisteredUsers.all().filter("username =", usern).get() 
            if not another_user:
                self.log_read(UnverifiedUsers, "Checking if username is available. ")
                another_user = UnverifiedUsers.all().filter("username =", usern).get()
            if another_user:
                have_error = True
                kw['error_username'] = "*"
                kw['error'] += 'That username is not available. '
            # Available email
            self.log_read(RegisteredUsers, "Checking if email is available. ")
            another_email = RegisteredUsers.all().filter("email =", email).get()
            if another_email:
                have_error = True
                kw['error_email'] = "*"
                kw['error'] += 'That email is already in use by someone. Did you <a href="/recover_password?email=%s">forget your password?. </a>' % email
            else:
                self.log_read(UnverifiedUsers, "Checking if email is available. ")
                another_email = UnverifiedUsers.all().filter("email =", email).get()
                if another_email:
                    have_error = True
                    kw['error_email'] = '*'
                    kw['error'] += 'This email is already registered but it still needs to be verified, click <a href="/verify_email?email=%s">here</a> to send the verification email again.' % email
        # Render
        if have_error:
            self.render('signup.html', **kw)
        else:
            salt = make_salt()
            ph = hash_str(password + salt)
            u = UnverifiedUsers(username = usern, password_hash = ph, salt = salt, email = email)
            self.log_and_put(u, "New user registration")
            u.send_verify_email()
            self.render("please_verify_email.html")

class LoginPage(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("login.html", username = username)

    def post(self):
        email_or_username = self.request.get('email_or_username')
        password = self.request.get('password')
        have_error = False
        kw = {'email_or_username' : email_or_username, 'password' : password, 'error' : ''}
        if not email_or_username:
            kw["error"] += "You must provide a valid email or username. "
            have_error = True
        if not password:
            kw["error"] += "You must provide your password. "
            have_error = True
        if not have_error:
            if re.match(EMAIL_RE, email_or_username):
                self.log_read(RegisteredUsers, "Checking user's login information. ")
                u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE email = :1", email_or_username).get()
            else:
                self.log_read(RegisteredUsers, "Checking user's login information. ")
                u = db.GqlQuery("SELECT * FROM RegisteredUsers WHERE username = :1", email_or_username).get() 
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
    def get(self, page_username):
        logged_in_user = self.get_user()
        self.log_read(RegisteredUsers, "Getting user instance of this page.")
        page_user = RegisteredUsers.all().filter("username =", page_username).get()
        kw = {"logged_in_user" : logged_in_user, "page_user" : page_user, "handler" : self}
        if not page_user:
            self.error(404)
            self.render("404.html")
            return
        if logged_in_user.key() == page_user.key():
            self.redirect("/settings")
            return
        if page_user.key() in logged_in_user.contacts:
            kw["is_contact"] = True
            kw["is_contact_message"] = '%s is in <a href="/contacts">your contacts</a> list.' % page_user.username
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
            kw["is_contact_message"] = '%s is not in <a href="/contacts">your contacts</a> list.' % page_user.username
            kw["button_message"] = "Add to contacts"
        self.render("user.html", **kw)
            
    def post(self, page_username):
        logged_in_user = self.get_user()
        if not logged_in_user:
            self.redirect("/login")
            return
        self.log_read(RegisteredUsers, "Getting user instance of this page.")
        page_user = RegisteredUsers.all().filter("username =", page_username).get()
        if not page_user:
            self.error(404)
            return
        if page_user.key() in logged_in_user.contacts:
            logged_in_user.contacts.remove(page_user.key())
            self.log_and_put(logged_in_user, "Removing a contact.")
        else:
            logged_in_user.contacts.append(page_user.key())
            self.log_and_put(logged_in_user, "Adding a contact.")
        self.redirect("/%s" % page_username)


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


class RecoverPasswordPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class VerifyEmailPage(GenericPage):
    def get(self):
        email = self.request.get("email")
        h = self.request.get("h")
        self.log_read(UnverifiedUsers)
        u = UnverifiedUsers.all().filter("email =", email).get()
        if not u:
            logging.warning("Handler VerifyEmailPage attempted to verify an email not in Datastore.")
            self.error(404)
            return 
        if hash_str(email + u.salt) == h:
            new_user = RegisteredUsers(username = u.username,
                                       email = u.email,
                                       salt = u.salt,
                                       password_hash = u.password_hash)
            self.log_and_put(new_user)
            self.log_and_delete(u)
            self.set_cookie("username", new_user.username, new_user.salt)
            self.render("email_verified.html")
        else:
            logging.warning("Handler VerifyEmailPage attempted to verify an email with the wrong hash.")
            self.error(404)
            return
