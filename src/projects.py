# projects.py
# For creating, managing and updating projects.

from generic import *
import email_messages

SHORT_DESCRIPTION_LENGTH = 150
UPDATES_TO_DISPLAY = 30           # number of updates to display in the Overview tab

###########################
##   Datastore Objects   ##
###########################

class Projects(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = False)
    authors = ndb.KeyProperty(repeated = True)                        # There's no such thing as an "owner"
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    default_open_p = ndb.BooleanProperty(default = True)
    wiki_open_p = ndb.BooleanProperty(default = True)
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
                                % (self.key, author_key))
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

    def add_author(self, requesting_handler, user):
        if user.key in self.authors: return False
        self.authors.append(user.key)
        self.wiki_notifications_list.append(user.key)
        self.nb_notifications_list.append(user.key)
        self.writings_notifications_list.append(user.key)
        self.code_notifications_list.append(user.key)
        self.datasets_notifications_list.append(user.key)
        self.forum_threads_notifications_list.append(user.key)
        self.forum_posts_notifications_list.append(user.key)
        requesting_handler.log_and_put(self, "Adding a new author. ")
        user.my_projects.append(self.key)
        requesting_handler.log_and_put(user, "Adding a new project to my_projects property")
        return True

    def list_updates(self, requesting_handler, user = None, n = UPDATES_TO_DISPLAY):
        assert type(n) == int
        assert n > 0
        requesting_handler.log_read(ProjectUpdates, "Requesting %s updates. " % n)
        updates = []
        for u in ProjectUpdates.query(ancestor = self.key).order(-ProjectUpdates.date).iter():
            if u.is_open_p() or (user and self.user_is_author(user)): updates.append(u)
            if len(updates) >= n: break            
        return updates


# Should have a Project as parent
class ProjectUpdates(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add = True)
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    item = ndb.KeyProperty(required = True)

    def description_html(self, project):
        return render_str("project_activity.html", author = self.author.get(), item = self.item.get(), project = project)

    def is_open_p(self):
        try:
            val = self.item.get().is_open_p()
        except:
            val = False
        return val


######################
##   Web Handlers   ##
######################

class ProjectPage(GenericPage):
    def get_project(self, projectid, log_message = ''):
        self.log_read(Projects, log_message)
        project = Projects.get_by_id(int(projectid))
        return project

    def put_and_report(self, item, author, project, other_to_update = None):
        self.log_and_put(item)
        # Log user activity
        u_activity = UserActivities(parent = author.key, item = item.key, relative_to = project.key, kind = "Projects")
        self.log_and_put(u_activity)
        # Log project update
        p_update = ProjectUpdates(parent = project.key, author = author.key, item = item.key)
        self.log_and_put(p_update)
        self.log_and_put(project)
        if other_to_update: self.log_and_put(other_to_update)
        return


class OverviewPage(ProjectPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        self.render("project_overview.html", project = project, 
                    overview_tab_class = "active",
                    authors = project.list_of_authors(self),
                    updates = project.list_updates(self, user, UPDATES_TO_DISPLAY),
                    visitor_p = not (user and project.user_is_author(user)))


class NewProjectPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/new_project")
            return
        self.render("project_new.html", user = user)

    def post(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/new_project")
            return
        have_error = False
        kw = {"error_message" : ''}
        p_name = self.request.get('p_name').strip()
        p_description = self.request.get('p_description')
        open_p = self.request.get("open_p") == "True"
        if not p_name:
            have_error = True
            kw["error_message"] = 'Please provide a name for your project. '
            kw["name_class"] = "has-error"
        if not p_description:
            have_error = True
            kw["error_message"] = 'Please provide a description of the project. '
            kw["description_class"] = "has-error"
        if have_error:
            self.render("project_new.html", user = user, p_name = p_name, p_description = p_description, **kw)
        else:
            new_project = Projects(name = p_name,
                                   description = p_description,
                                   default_open_p = open_p,
                                   wiki_open_p = open_p,
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
            self.redirect("/%s" % new_project.key.integer_id())


class AdminPage(ProjectPage):
    def render(self, *a, **kw):
        ProjectPage.render(self, admin_tab_class = "active", *a, **kw)

    def get(self, projectid):
        user = self.get_login_user()
        h = self.request.get("h")           # This will be present if a new user is invited to the project.
        if not user:
            goback = '/' + projectid + '/admin'
            if h: goback += "?h=" + h
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found" % projectid)
            return
        # New user here?
        if h and (hash_str(user.salt + str(project.key)) == h):
            project.add_author(self, user)
            self.redirect("/%s/admin" % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s" % projectid)
            return
        kw = {"wiki_p"          : "checked" if user.key in project.wiki_notifications_list else "",
              "notebooks_p"     : "checked" if user.key in project.nb_notifications_list else "",
              "writings_p"      : "checked" if user.key in project.writings_notifications_list else "",
              "code_p"          : "checked" if user.key in project.code_notifications_list else "",
              "datasets_p"      : "checked" if user.key in project.datasets_notifications_list else "",
              "forum_threads_p" : "checked" if user.key in project.forum_threads_notifications_list else "",
              "forum_posts_p"   : "checked" if user.key in project.forum_posts_notifications_list else "",
              "p_description"   : project.description,
              "p_name"          : project.name,
              "authors"         : project.list_of_authors(self)}
        self.render('project_admin.html', project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/admin'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found" % projectid)
            return
        kw = {"wiki_p"          : self.request.get("wiki_p"),
              "notebooks_p"     : self.request.get('notebooks_p'),
              "writings_p"      : self.request.get('writings_p'),
              "code_p"          : self.request.get('code_p'),
              "datasets_p"      : self.request.get('datasets_p'),
              "forum_threads_p" : self.request.get('forum_threads_p'),
              "forum_posts_p"   : self.request.get('forum_posts_p'),
              "p_description"   : self.request.get('p_description'),
              "p_name"          : self.request.get('p_name'),
              "default_open_p"  : self.request.get('open_p') == 'True',
              "authors"         : project.list_of_authors(self)}
        have_error = False
        kw["error"] = ''
        if not project.user_is_author(user):
            self.redirect("/%s" % projectid)
            return
        ## Project's name and description
        if kw["p_name"]:
            project.name = kw["p_name"]
        else:
            have_error = True
            kw["error"] = "You must provide a name for your project. "
            kw["nClass"] = "has-error"
        if kw["p_description"]:
            project.description = kw["p_description"]
        else:
            have_error = True
            kw["error"] += "You must provide a description for the project. "
            kw["dClass"] = "has-error"
        project.default_open_p = kw["default_open_p"]
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
        self.render('project_admin.html', project = project, **kw)
        

class InvitePage(ProjectPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/invite'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found" % projectid)
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        kw = {"title" : "Invite a new collaborator",
              "subtitle" : "Use this form to make an email invitation for a user to collaborate in your project.",
              "name_placeholder" : "Write here the name of the user you want to invite.",
              "content_placeholder" : "Write here a brief invitation message.",
              "submit_button_text" : "Send invitation",
              "cancel_url" : "/%s/admin" % projectid,
              "breadcrumb" : '<li class="active">Admin</li>',
              "markdown_p" : True}
        self.render("project_form_2.html", project = project, admin_tab_class = "acctive", **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/invite'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found" % projectid)
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return        
        kw = {"title" : "Invite a new collaborator",
              "subtitle" : "Use this form to make an email invitation for a user to collaborate in your project.",
              "name_placeholder" : "Write here the name of the user you want to invite.",
              "content_placeholder" : "Write here a brief invitation message.",
              "submit_button_text" : "Send invitation",
              "cancel_url" : "/%s/admin" % projectid,
              "breadcrumb" : '<li class="active">Admin</li>',
              "markdown_p" : True}
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
            email_messages.send_invitation_to_project(project = project, inviting = user, invited = i_user, message = kw["content_value"])
            kw["info_message"] = "Invitation sent"
            kw["name_value"] = ''
            kw["content_value"] = ''
        self.render("project_form_2.html", project = project, admin_tab_class = "active", **kw)
