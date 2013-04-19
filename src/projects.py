# projects.py
# For creating, managing and updating projects.

from generic import *
import email_messages

SHORT_DESCRIPTION_LENGTH = 150

###########################
##   Datastore Objects   ##
###########################

class Projects(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = False)
    authors = ndb.KeyProperty(repeated = True)                        # There's no such thing as an "owner"
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    # Lists of authors to send notifications after an update
    wiki_notifications_list = ndb.KeyProperty(repeated = True)
    nb_notifications_list = ndb.KeyProperty(repeated = True)
    writings_notifications_list = ndb.KeyProperty(repeated = True)
    code_notifications_list = ndb.KeyProperty(repeated = True)
    datasets_notifications_list = ndb.KeyProperty(repeated = True)
    forum_threads_notifications_list = ndb.KeyProperty(repeated = True)
    forum_posts_notifications_list = ndb.KeyProperty(repeated = True)


    def list_of_authors(self, requesting_handler):
        authors_list = []
        for author_key in self.authors:
            requesting_handler.log_read(RegisteredUsers, "Getting an author from a Project's list of authors. ")
            author = author_key.get()
            if author: 
                authors_list.append(author)
            else:
                logging.warning("Project with key (%s) contains a broken reference to author (%s)" 
                                % (self.key(), author_key))
        return authors_list

    def user_is_author(self, user):
        result = False
        for author_key in self.authors:
            if user.key == author_key: result = True
        return result

    def short_description(self):
        if len(self.description) < SHORT_DESCRIPTION_LENGTH:
            return self.description
        else:
            return self.description[0:SHORT_DESCRIPTION_LENGTH - 3] + "..."

    def add_author(self, user):
        if user.key in self.authors: return False
        self.authors.append(user.key)
        self.wiki_notifications_list.append(user.key)
        self.nb_notifications_list.append(user.key)
        self.writings_notifications_list.append(user.key)
        self.code_notifications_list.append(user.key)
        self.datasets_notifications_list.append(user.key)
        self.forum_threads_notifications_list.append(user.key)
        self.forum_posts_notifications_list.append(user.key)
        logging.debug("DB WRITE: Adding a new author to project %s" % self.name)
        self.put()
        user.my_projects.append(self.key)
        logging.debug("DB WRITE: Adding a new project to %s my_projects property" %  user.__class__.__name__)
        user.put()
        return True

######################
##   Web Handlers   ##
######################

class ProjectPage(GenericPage):
    def get_project(self, p_author, projectid, message = ''):
        logging.debug("DB READ: Handler %s requests an instance of Projects. %s"
                      % (self.__class__.__name__, message))
        project = Projects.get_by_id(int(projectid))
        if project.user_is_author(p_author): 
            return project
        else:
            return False

    def add_notifications(self, category, author, users_to_notify, html, txt):
        for u in users_to_notify:
            notification = EmailNotifications(author = author.key, category = category, html = html, txt = txt,
                                              sent = False, parent = u)
            self.log_and_put(notification)
        return


class OverviewPage(ProjectPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key "%s" not found' % projectid)
            return
        self.render("project_overview.html", p_author = p_author, project = project, authors = project.list_of_authors(self))


class NewProjectPage(GenericPage):
    def get(self, username):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/new_project'
            self.redirect("/login?goback=%s" % goback)
            return
        if not username.lower() == user.username:
            self.redirect("/%s/new_project" % user.username)
            return
        self.render("project_new.html", user = user)

    def post(self, username):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/new_project'
            self.redirect("/login?goback=%s" % goback)
            return
        if not username.lower() == user.username:
            self.redirect("/%s/new_project" % user.username)
        have_error = False
        error_message = ''
        p_name = self.request.get('p_name').strip()
        p_description = self.request.get('p_description')
        if not p_name:
            have_error = True
            error_message = 'Please provide a name for your project. '
        if not p_description:
            have_error = True
            error_message = 'Please provide a description of the project. '
        if have_error:
            self.render("project_new.html", user = user, p_name = p_name, p_description = p_description,
                        error_message = error_message)
        else:
            new_project = Projects(name = p_name,
                                   description = p_description,
                                   authors = [user.key],
                                   wiki_notifications_list = [user.key],
                                   nb_notifications_list = [user.key],
                                   writings_notifications_list = [user.key],
                                   code_notifications_list = [user.key],
                                   datasets_notifications_list = [user.key],
                                   forum_threads_notifications_list = [user.key],
                                   forum_posts_notifications_list = [user.key])
            self.log_and_put(new_project, "Creating a new project. ")
            user.my_projects.append(new_project.key)
            self.log_and_put(user, "Appending a project to a RegisteredUser's my_projects list ")
            self.redirect("/%s/%s" % (user.username, new_project.key.integer_id()))


class AdminPage(ProjectPage):
    def get(self, username, projectid):
        user = self.get_login_user()
        h = self.request.get("h")           # This will be present if a new user is invited to the project.
        if not user:
            goback = '/' + username + '/' + projectid + '/admin'
            if h: goback += "?h=" + h
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        # New user here?
        if h and (hash_str(username + user.username + str(project.key)) == h):
            project.add_author(user)
            self.redirect("/%s/%s/admin" % (user.username, projectid))
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        if not user.key == p_author.key:
            self.redirect("/%s/%s/admin" % (user.username, projectid))
            return
        kw = {"wiki_p"          : "checked" if user.key in project.wiki_notifications_list else "",
              "notebooks_p"     : "checked" if user.key in project.nb_notifications_list else "",
              "writings_p"      : "checked" if user.key in project.writings_notifications_list else "",
              "code_p"          : "checked" if user.key in project.code_notifications_list else "",
              "datasets_p"      : "checked" if user.key in project.datasets_notifications_list else "",
              "forum_threads_p" : "checked" if user.key in project.forum_threads_notifications_list else "",
              "forum_posts_p"   : "checked" if user.key in project.forum_posts_notifications_list else "",
              "p_description"   : project.description,
              "authors"         : project.list_of_authors(self)}
        self.render('project_admin.html', p_author = p_author, project = project, **kw)

    def post(self, username, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/admin'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        kw = {"wiki_p"          : self.request.get("wiki_p"),
              "notebooks_p"     : self.request.get('notebooks_p'),
              "writings_p"      : self.request.get('writings_p'),
              "code_p"          : self.request.get('code_p'),
              "datasets_p"      : self.request.get('datasets_p'),
              "forum_threads_p" : self.request.get('forum_threads_p'),
              "forum_posts_p"   : self.request.get('forum_posts_p'),
              "p_description"   : self.request.get('p_description'),
              "authors"         : project.list_of_authors(self)}

        have_error = False
        kw["error"] = ''
        ## Project description
        if kw["p_description"]:
            project.description = kw["p_description"]
        else:
            have_error = True
            kw["error"] = "You must provide a description for the project. "

        ## Email notifications
        # Add to list
        if kw["wiki_p"] and not (user.key in project.wiki_notifications_list):
            project.wiki_notifications_list.append(user.key)
        if kw["notebooks_p"] and not (user.key in project.nb_notifications_list):
            project.nb_notifications_list.append(user.key)
        if kw["writings_p"] and not (user.key in project.writings_notifications_list):
            project.writings_notifications_list.append(user.key)
        if kw["code_p"] and not (user.key in project.code_notifications_list):
            project.code_notifications_list.append(user.key)
        if kw["datasets_p"] and not (user.key in project.datasets_notifications_list):
            project.datasets_notifications_list.append(user.key)
        if kw["forum_threads_p"] and not (user.key in project.forum_threads_notifications_list):
            project.forum_threads_notifications_list.append(user.key)
        if kw["forum_posts_p"] and not (user.key in project.forum_posts_notifications_list):
            project.forum_posts_notifications_list.append(user.key)
        # Remove from list
        if (not kw["wiki_p"]) and (user.key in project.wiki_notifications_list):
            project.wiki_notifications_list.remove(user.key)
        if (not kw["notebooks_p"]) and (user.key in project.nb_notifications_list):
            project.nb_notifications_list.remove(user.key)
        if (not kw["writings_p"]) and (user.key in project.writings_notifications_list):
            project.writings_notifications_list.remove(user.key)
        if (not kw["code_p"]) and (user.key in project.code_notifications_list):
            project.code_notifications_list.remove(user.key)
        if (not kw["datasets_p"]) and (user.key in project.datasets_notifications_list):
            project.datasets_notifications_list.remove(user.key)
        if (not kw["forum_threads_p"]) and (user.key in project.forum_threads_notifications_list):
            project.forum_threads_notifications_list.remove(user.key)
        if (not kw["forum_posts_p"]) and (user.key in project.forum_posts_notifications_list):
            project.forum_posts_notifications_list.remove(user.key)
    
        if not have_error:
            self.log_and_put(project, "Updating email notifications and/or description. ")
            kw["info_message"] = "Changes saved"
        self.render('project_admin.html', p_author = p_author, project = project, **kw)
        

class InvitePage(ProjectPage):
    def get(self, username, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/invite'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        kw = {"title" : "Invite a new collaborator",
              "subtitle" : "Use this form to make an email invitation for a user to collaborate in your project.",
              "name_placeholder" : "Write here the name of the user you want to invite.",
              "content_placeholder" : "Write here a brief invitation message.",
              "submit_button_text" : "Send invitation",
              "cancel_url" : "/%s/%s/admin" % (username, projectid),
              "title_bar_extra" : '/ <a href="/%s/%s/admin">Admin</a>' % (username, projectid),
              "more_head" : "<style>.admin-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/invite'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return        
        kw = {"title" : "Invite a new collaborator",
              "subtitle" : "Use this form to make an email invitation for a user to collaborate in your project.",
              "name_placeholder" : "Write here the name of the user you want to invite.",
              "content_placeholder" : "Write here a brief invitation message.",
              "submit_button_text" : "Send invitation",
              "cancel_url" : "/%s/%s/admin" % (username, projectid),
              "title_bar_extra" : '/ <a href="/%s/%s/admin">Admin</a>' % (username, projectid),
              "more_head" : "<style>.admin-tab {background: white;}</style>"}
        have_error = False
        kw["name_value"] = self.request.get("name")
        kw["content_value"] = self.request.get("content")
        if (not kw["name_value"]) or (not kw["content_value"]):
            have_error = True
            kw["error_message"] = "You must provide the name of the user to invite and a content for your invitation."
        i_user = self.get_user_by_username(kw["name_value"].lower())
        if not i_user:
            have_error = True
            kw["error_message"] = "User <em>%s</em> doesn't exist. " % kw["name_value"]
        if i_user and project.user_is_author(i_user):
            have_error = True
            kw["error_message"] = "User <em>%s</em> is already a collaborator in this project. " % kw["name_value"]
        if not have_error:
            email_messages.send_invitation_to_project(project = project, inviting = user, invited = i_user)
            kw["info_message"] = "Invitation sent"
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)
