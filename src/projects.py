# projects.py
# For creating, managing and updating projects.

from generic import *
from notebooks import Notebooks

SHORT_DESCRIPTION_LENGTH = 150
PROJECT_NAME_REGEXP = r'^[a-zA-Z0-9\s-]+$'

###########################
##   Datastore Objects   ##
###########################

# Parent of ProjectEntries
class Projects(db.Model):
    name = db.StringProperty(required = True)
    description = db.TextProperty(required = False)
    authors = db.ListProperty(db.Key)                        # There's no such thing as an "owner"
    started = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)
    references = db.ListProperty(db.Key)
    notebooks = db.ListProperty(db.Key)
    # Lists of authors to send notifications after an update
    wiki_notifications_list = db.ListProperty(db.Key)
    nb_notifications_list = db.ListProperty(db.Key)
    writings_notifications_list = db.ListProperty(db.Key)
    code_notifications_list = db.ListProperty(db.Key)
    datasets_notifications_list = db.ListProperty(db.Key)
    forum_threads_notifications_list = db.ListProperty(db.Key)
    forum_posts_notifications_list = db.ListProperty(db.Key)


    def list_of_authors(self, requesting_handler):
        authors_list = []
        for author_key in self.authors:
            requesting_handler.log_read(RegisteredUsers, "Getting an author from a Project's list of authors. ")
            author = db.Query().filter("__key__ =", author_key).get()
            if author: 
                authors_list.append(author)
            else:
                logging.warning("Project with key (%s) contains a broken reference to author (%s)" 
                                % (self.key(), author_key))
        return authors_list

    def user_is_author(self, user):
        result = False
        for author_key in self.authors:
            if user.key() == author_key: result = True
        return result

    def short_description(self):
        if len(self.description) < SHORT_DESCRIPTION_LENGTH:
            return self.description
        else:
            return self.description[0:SHORT_DESCRIPTION_LENGTH - 3] + "..."


######################
##   Web Handlers   ##
######################

class OverviewPage(GenericPage):
    def get(self, username, project_name):
        p_user = self.get_user_by_username(username)
        if not p_user:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_user):
                project = p
                break
        if not project:
            self.error(404)
            self.render("404.html")
            return
        self.render("project_overview.html", p_user = p_user, project = project, p_author = p_user, authors = project.list_of_authors(self))


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
        p_name = self.request.get('p_name').replace("_", " ").strip()
        p_description = self.request.get('p_description')
        if not p_name:
            have_error = True
            error_message = 'Please provide a name for your project. '
        if not p_description:
            have_error = True
            error_message = 'Please provide a description of the project. '
        if p_name and (not re.match(PROJECT_NAME_REGEXP, p_name)):
            have_error = True
            error_message = 'Invalid project name. Please user only letters, numbers, spaces and dashes. '
        if p_name and p_name.lower() == 'new project':
            have_error = True
            error_message = 'Invalid project name. Please choose a different name. '
        # Check for duplicate project names.
        duplicate_p = False
        for p_key in user.my_projects:
            if self.get_item_from_key(p_key).name == p_name.lower().replace(" ", "_"):
                duplicate_p = True
                break
        if duplicate_p:
            have_error = True
            error_message = "There is already a project with the same name. Please choose a different one. "
        if have_error:
            self.render("project_new.html", user = user, p_name = p_name, p_description = p_description,
                        error_message = error_message)
        else:
            new_project = Projects(name = p_name.lower().replace(" ","_"),
                                   description = p_description,
                                   authors = [user.key()],
                                   references = [], notebooks = [],
                                   wiki_notifications_list = [user.key()],
                                   nb_notifications_list = [user.key()],
                                   writings_notifications_list = [user.key()],
                                   code_notifications_list = [user.key()],
                                   datasets_notifications_list = [user.key()],
                                   forum_threads_notifications_list = [user.key()],
                                   forum_posts_notifications_list = [user.key()])
            self.log_and_put(new_project, "Creating a new project. ")
            user.my_projects.append(new_project.key())
            self.log_and_put(user, "Appending a project to a RegisteredUser's my_projects list ")
            self.redirect("/%s/%s" % (user.username, new_project.name))


class AdminPage(GenericPage):
    def get(self, username, projectname):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/admin'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = False
        for p in Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        if not user.key() == p_author.key():
            self.redirect("/%s/%s/admin" % (user.username, projectname))
            return
        kw = {"wiki_p"          : "checked" if user.key() in project.wiki_notifications_list else "",
              "notebooks_p"     : "checked" if user.key() in project.nb_notifications_list else "",
              "writings_p"      : "checked" if user.key() in project.writings_notifications_list else "",
              "code_p"          : "checked" if user.key() in project.code_notifications_list else "",
              "datasets_p"      : "checked" if user.key() in project.datasets_notifications_list else "",
              "forum_threads_p" : "checked" if user.key() in project.forum_threads_notifications_list else "",
              "forum_posts_p"   : "checked" if user.key() in project.forum_posts_notifications_list else ""}
        self.render('project_admin.html', p_author = p_author, project = project, **kw)

    def post(self, username, projectname):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/admin'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.render("404.html")
            return
        project = False
        for p in Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        if not project.user_is_author(user):
            self.write("You are not a member of this project.")
            return
        kw = {"wiki_p" : self.request.get("wiki_p"),
              "notebooks_p" : self.request.get('notebooks_p'),
              "writings_p" : self.request.get('writings_p'),
              "code_p" : self.request.get('code_p'),
              "datasets_p" : self.request.get('datasets_p'),
              "forum_threads_p" : self.request.get('forum_threads_p'),
              "forum_posts_p" : self.request.get('forum_posts_p')}
        # Add to list
        if kw["wiki_p"] and not (user.key() in project.wiki_notifications_list):
            project.wiki_notifications_list.append(user.key())
        if kw["notebooks_p"] and not (user.key() in project.nb_notifications_list):
            project.nb_notifications_list.append(user.key())
        if kw["writings_p"] and not (user.key() in project.writings_notifications_list):
            project.writings_notifications_list.append(user.key())
        if kw["code_p"] and not (user.key() in project.code_notifications_list):
            project.code_notifications_list.append(user.key())
        if kw["datasets_p"] and not (user.key() in project.datasets_notifications_list):
            project.datasets_notifications_list.append(user.key())
        if kw["forum_threads_p"] and not (user.key() in project.forum_threads_notifications_list):
            project.forum_threads_notifications_list.append(user.key())
        if kw["forum_posts_p"] and not (user.key() in project.forum_posts_notifications_list):
            project.forum_posts_notifications_list.append(user.key())
        # Remove from list
        if (not kw["wiki_p"]) and (user.key() in project.wiki_notifications_list):
            project.wiki_notifications_list.remove(user.key())
        if (not kw["notebooks_p"]) and (user.key() in project.nb_notifications_list):
            project.nb_notifications_list.remove(user.key())
        if (not kw["writings_p"]) and (user.key() in project.writings_notifications_list):
            project.writings_notifications_list.remove(user.key())
        if (not kw["code_p"]) and (user.key() in project.code_notifications_list):
            project.code_notifications_list.remove(user.key())
        if (not kw["datasets_p"]) and (user.key() in project.datasets_notifications_list):
            project.datasets_notifications_list.remove(user.key())
        if (not kw["forum_threads_p"]) and (user.key() in project.forum_threads_notifications_list):
            project.forum_threads_notifications_list.remove(user.key())
        if (not kw["forum_posts_p"]) and (user.key() in project.forum_posts_notifications_list):
            project.forum_posts_notifications_list.remove(user.key())
        self.log_and_put(project, "Updating email notifications")
        kw["info_message"] = "Changes saved"
        self.render('project_admin.html', p_author = p_author, project = project, **kw)
        
