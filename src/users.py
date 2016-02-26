# users.py
# All related to user login/signup and preferences storage.

import generic, projects, email_messages, secrets, simpleauth, groups
import bibliography, code, collab_writing, datasets, forum, images, notebooks, wiki
import hashlib, re, logging, json
from google.appengine.api import mail, urlfetch
from webapp2_extras import auth

LOGIN_COOKIE_MAXAGE = 604800 # In seconds; 604800s = 1 week
EMAIL_RE = r'^[\S]+@[\S]+\.[\S]+$'
USERNAME_RE = r'^[a-zA-Z][a-zA-Z0-9_-]{2,20}$'
PASSWORD_RE = r'^.{3,20}$'
FORBIDDEN_USERNAMES = ["login", "logout", "signup", "settings","recover_password","verify_email",
                       "cron", "new_project", "file", "recover_password", "terms", "new_group", "g"]

class LoginPage(generic.GenericPage):
    def get(self):
        kw = {'user': self.get_login_user(),
              'goback' : self.request.get('goback'),
              'r_error_message' : self.request.get('r_error_message'),
              'info' : self.request.get('info')}
        if kw['user']: 
            self.redirect("%s" % kw["goback"] if kw["goback"] else "/")
            return
        self.render("login.html", **kw)

    def post(self):
        email_or_username = self.request.get('email_or_username')
        password = self.request.get('password')
        have_error = False
        kw = {'email_or_username' : email_or_username, 'password' : password, 'error_message' : '', 'goback' : self.request.get('goback')}
        if not email_or_username:
            kw["error_message"] += "You must provide a valid email or username. "
            kw["uname_error_p"] = True
            have_error = True
        if not password:
            kw["error_message"] += "You must provide your password. "
            kw["pwd_error_p"] = True
            have_error = True
        if not have_error:
            if re.match(EMAIL_RE, email_or_username):
                u = self.get_user_by_email(email_or_username, "Checking user's login information. ")
            else:
                u = self.get_user_by_username(email_or_username.lower(), "Checking user's login information. ")
            if (not u) or (u.password_hash != generic.hash_str(password + u.salt)):
                kw["error_message"] = 'Invalid password. If you forgot your password try setting a new one with the form below.'
                have_error = True
                kw["pwd_error_p"] = True
        if have_error:
            self.render("login.html", **kw)
        else:
#            u.salt = generic.make_salt()
#            u.password_hash = generic.hash_str(password + u.salt)
#            self.log_and_put(u, "Making new salt. ")
            self.set_cookie("username", u.username, u.salt, max_age = LOGIN_COOKIE_MAXAGE)
            if kw['goback']: 
                self.redirect(kw['goback'])
                return
            self.redirect("/%s" % u.username)


class UserPage(generic.GenericPage):
    def get(self, username):
        page_user = self.get_user_by_username(username)
        if not page_user:
            self.error(404)
            self.render("404.html", info = "User <em>%s</em> not found." % username)
            return
        user = self.get_login_user()
        kw = {"projects" : page_user.list_of_projects(),
              "self_user_p" : user and (user.key == page_user.key),
              "recent_actv" : page_user.get_recent_activity(days=7),
              "p_stats" : {"Notebooks" : 0, "Code" : 0, "Datasets" : 0, "Wiki" : 0, "Writings" : 0,"Forum" : 0,"Bibliography" : 0,
                           "Images" : 0},
              "p_counts" : page_user.get_project_contributions_counts(30, page_user.key == user.key if user else False),
              "plusone_p": True,
              "show_project_p": True}
        for a in kw["recent_actv"]["Projects"]:
            if a.is_open_p() or (user and a.actv_kind == "Projects" and a.relative_to.get().user_is_author(user)):
                if a.item.kind() in ["Notebooks", "NotebookNotes", "NoteComments"]: kw["p_stats"]["Notebooks"] += 1
                elif a.item.kind() in ["CodeRepositories", "CodeComments"]: kw["p_stats"]["Code"] += 1
                elif a.item.kind() in ["DataSets", "DataConcepts", "DataRevisions"]: kw["p_stats"]["Datasets"] += 1
                elif a.item.kind() in ["WikiRevisions"]: kw["p_stats"]["Wiki"] += 1
                elif a.item.kind() in ["CollaborativeWritings", "WritingRevisions", "WritingComments"]: kw["p_stats"]["Writings"] += 1
                elif a.item.kind() in ["ForumThreads", "ForumComments"]: kw["p_stats"]["Forum"] += 1
                elif a.item.kind() in ["BiblioItems", "BiblioComments"]: kw["p_stats"]["Bibliography"] += 1
                elif a.item.kind() in ["Images"]: kw["p_stats"]["Images"] += 1
        self.render("user.html", page_user = page_user, **kw)


class SignupPage(generic.GenericPage):
    def get(self):
        user = self.get_login_user()
        kw = {"email" : self.request.get("email"),
              "info" : self.request.get("info")}
        if kw["email"]:
            kw["error"] = "The email %s is not registered yet. Please create a new account first. " % kw["email"]
        self.render("signup.html", user = user, **kw)


    def post(self):
        usern = self.request.get('usern')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        have_error = False
        kw = {"usern" : usern, "email" : email, "error" : '', "info" : self.request.get("info")}
        # Valid input
        if usern and (usern.lower() in FORBIDDEN_USERNAMES):
            kw['error_username'] = True
            kw['error'] = "That username is not available"
            have_error = True
        if not re.match(USERNAME_RE, usern):
            kw['error_username'] = True
            kw['error'] += "That's not a valid username, it must be from 3 to 20 characters long, start with a letter and contain only letters, numbers, dashes and underscores. "
            have_error = True
        if not re.match(EMAIL_RE, email):
            kw['error_email'] = True
            kw['error'] += "That doesn't seem like a valid email. "
            have_error = True
        if not re.match(PASSWORD_RE, password):
            kw['error_password'] = True
            kw['error'] += "That's not a valid password, it must be between 3 and 20 characters long. "
            have_error = True
        elif password != verify:
            kw['error_verify'] = True
            kw['error'] += "Your passwords didn't match. "
            have_error = True
        if not have_error:
            usern = usern.lower()
            # Available username
            another_user = self.get_user_by_username(usern, "Checking if username is available")
            if not another_user:
                self.log_read(generic.UnverifiedUsers, "Checking if username is available. ")
                another_user = generic.UnverifiedUsers.query(generic.UnverifiedUsers.username == usern).get()
            if another_user:
                have_error = True
                kw['error_username'] = True
                kw['error'] += 'That username is not available. '
            # Available email
            another_email = self.get_user_by_email(email, "Checking if email is available. ")
            if another_email:
                have_error = True
                kw['error_email'] = True
                kw['error'] += 'That email is already in use by someone. Did you <a href="/recover_password?email=%s">forget your password?. </a>' % email
            else:
                self.log_read(generic.UnverifiedUsers, "Checking if email is available. ")
                another_email = generic.UnverifiedUsers.query(generic.UnverifiedUsers.email == email).get()
                if another_email:
                    have_error = True
                    kw['error_email'] = True
                    kw['error'] = 'This email is already registered but it still needs to be verified, click <a href="/verify_email?email=%s">here</a> to send the verification email again.' % email
        # Render
        if have_error:
            self.render('signup.html', **kw)
        else:
            salt = generic.make_salt()
            ph = generic.hash_str(password + salt)
            u = generic.UnverifiedUsers(username = usern, password_hash = ph, salt = salt, email = email)
            self.log_and_put(u, "New user registration")
            email_messages.send_verify_email(u)
            self.render('signup.html', info = "A message has been sent to your email, please follow the instructions provided there.")


class SettingsPage(generic.GenericPage):
    def get(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/settings")
            return
        kw = {"usern"    : user.username, 
              "email"    : user.email,
              "about_me" : user.about_me if user.about_me else '',
              "gplusid"  : user.gplusid if user.gplusid else '',
              "info"     : self.request.get("info"),
              "plusone_p": True}
        self.render("settings.html", user = user, **kw)

    def post(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login", goback = "/settings")
            return
        kw = {"usern"    : self.request.get("usern").strip(),
              "email"    : self.request.get("email").strip(),
              "about_me" : self.request.get("about_me").strip(),
              "gplusid"  : user.gplusid if user.gplusid else '',
              "plusone_p": True}
        have_error = False
        if kw["usern"]: kw["usern"] = kw["usern"].lower()
        if user.username != kw["usern"]:
            u2 = self.get_user_by_username(kw["usern"], "Checking if new username is available. ")
            if u2 or (not re.match(USERNAME_RE, kw["usern"])):
                kw["error_username"] = "*"
                kw['error'] = "Sorry, that username is not available. "
                have_error = True
        if user.email != kw["email"]:
            u2 = self.get_user_by_email(kw["email"], "Checking if new email is available. ")
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
            if user.gplusid: user.set_gplus_profile()
            self.log_and_put(user, "Updating settings.")
            user.set_profile_image_url("google" if user.gplus_profile_json else "gravatar")
            self.set_cookie("username", user.username, user.salt, max_age = LOGIN_COOKIE_MAXAGE)
            self.redirect("/settings?info=Changes saved")


class RecoverPasswordPage(generic.GenericPage):
    def get(self):
        email = self.request.get('email')
        key = self.request.get('k')
        have_error = False
        if (not email) or (not key):
            have_error = True
            error = "Malformed url, please try again. "
        user = self.get_user_by_email(email)
        if not user:
            have_error = True
            error = "There's not a user with that email %s" % email            
        else:
            if not key == generic.hash_str(user.username + user.salt):
                have_error = True
                error = "Malformed url, please try again. "
        if have_error:
            self.redirect("/login?error=%s" % error)
        else:
            self.render("recover_password.html", email = email, key = key, error = self.request.get("error"))

    def post(self):
        action = self.request.get('action')
        have_error = False
        email = self.request.get("email")
        if action == "send_email":
            if (not email) or (not re.match(EMAIL_RE, email)):
                have_error = True
                r_error_message = "Please write a valid email."
            if not have_error:
                user = self.get_user_by_email(email)
                if not user:
                    have_error = True
                    r_error_message = "That's not a registered email."
            if have_error:
                self.redirect("/login?r_error_message=%s" % r_error_message)
            else:
                link = '%s/recover_password?email=%s&k=%s' % (generic.APP_URL, email, generic.hash_str(user.username + user.salt))
                message = mail.EmailMessage(sender = generic.APP_NAME + ' <' + generic.ADMIN_EMAIL + '>',
                                            to = email,
                                            subject = 'Password recovery',
                                            body = generic.render_str('emails/recover_password.txt',  reset_link = link, ADMIN_EMAIL = generic.ADMIN_EMAIL),
                                            html = generic.render_str('emails/recover_password.html', reset_link = link, ADMIN_EMAIL = generic.ADMIN_EMAIL))
                if generic.DEBUG: logging.debug("EMAIL: Sending an email for password recovery. ")
                message.send()
                self.redirect('/login?info=Email sent. To reset your password follow the instructions on the email.')
        elif action == "do_reset":
            password = self.request.get("password")
            p_repeat = self.request.get("p_repeat")
            key = self.request.get("k")
            if not (email and key):
                have_error = True
            if not (password and p_repeat and re.match(PASSWORD_RE, password) and password == p_repeat):
                self.redirect('/recover_password?email=%s&k=%s&error=%s' % (email, key, "Please fill both boxes with the same password. "))
                return
            if not have_error:
                user = self.get_user_by_email(email)
                if not user:
                    have_error = True
                elif not key == generic.hash_str(user.username + user.salt):
                    have_error = True
            if have_error:
                self.error(400)
                error = "Invalid request. "
                self.write(error)
            else:
                salt = generic.make_salt()
                user.salt = salt
                user.password_hash = generic.hash_str(password + salt)
                self.log_and_put(user)
                self.redirect("/login?info=Password successfully changed, you can login now with your new password.")


class VerifyEmailPage(generic.GenericPage):
    def get(self):
        username = self.request.get("username")
        email = self.request.get("email").strip()
        if email:
            u = generic.UnverifiedUsers.query(generic.UnverifiedUsers.email == email).get()
            if u:
                email_messages.send_verify_email(u)
                self.redirect("signup?info=A message has been sent to your email, please follow the instructions provided there.")
                return
        h = self.request.get("h")
        self.log_read(generic.UnverifiedUsers)
        u = generic.UnverifiedUsers.query(generic.UnverifiedUsers.username == username).get()
        if not u:
            logging.warning("Handler VerifyEmailPage attempted to verify an email not in Datastore.")
            self.error(404)
            return 
        if generic.hash_str(username + u.salt) == h:
            new_user = generic.RegisteredUsers(username = u.username,
                                               password_hash = u.password_hash,
                                               salt = u.salt,
                                               email = u.email,
                                               about_me = '',
                                               my_projects = [],
                                               profile_image_url = "https://secure.gravatar.com/avatar/" + hashlib.md5(u.email.strip().lower()).hexdigest())
            self.log_and_put(new_user)
            self.log_and_delete(u)
            self.set_cookie("username", new_user.username, new_user.salt, max_age = LOGIN_COOKIE_MAXAGE)
            self.render("email_verified.html")
        else:
            logging.warning("Handler VerifyEmailPage attempted to verify an email with the wrong hash.")
            self.error(404)
            return

class AuthHandler(generic.GenericPage, simpleauth.SimpleAuthHandler):
    """Authentication handler for all kinds of auth."""

    # Enable optional OAuth 2.0 CSRF guard
    OAUTH2_CSRF_STATE = True

    def _on_signin(self, data, auth_info, provider):
        """Callback whenever a new or existing user is logging in.
        data is a user info dictionary.
        auth_info contains access token or oauth token and secret.

        See what's in it with logging.info(data, auth_info)
        """
        # Test if we already have a registered user
        user = self.get_user_by_email(data['email'])
        new_user_p = False
        if not user:
            prefix = data['email'].split("@")[0]
            test_user = self.get_user_by_username(prefix)
            username = ("g." + prefix) if test_user else prefix
            salt = generic.make_salt()
            user = generic.RegisteredUsers(username = username,
                                           password_hash = generic.hash_str(generic.make_salt() + salt),
                                           salt = salt,
                                           email = data['email'])
            if data['id']: 
                user.gplusid = data['id']
                user.set_gplus_profile()
                try: 
                    user.about_me = user.gplus_profile_json['aboutMe']
                except:
                    pass
            if data['picture']: user.profile_image_url = data['picture']
            self.log_and_put(user)
            new_user_p = True
        if (not new_user_p) and data['id']:
            try:
                user.gplusid = data['id']                
                user.set_gplus_profile()
                user.set_profile_image_url(provider = "google")
            except:
                logging.error("There was a problem fetching a gplus profile and/or profile image url for an existing user. ")
        self.set_cookie("username", user.username, user.salt, max_age = LOGIN_COOKIE_MAXAGE)
        self.redirect("/settings" if new_user_p else "/")

        
    def logout(self):
        self.remove_cookie("username")
        self.auth.unset_session()
        self.redirect('/')

    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """Should return a tuple (key, secret) for auth init requests.
        For OAuth 2.0 you should also return a scope, e.g.
        ('my app id', 'my app secret', 'email,user_about_me')
        
        The scope depends solely on the provider.
        See example/secrets.py.template
        """
        return secrets.AUTH_CONFIG[provider]
