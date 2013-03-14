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
                                   references = [], notebooks = [])
            self.log_and_put(new_project, "Creating a new project. ")
            user.my_projects.append(new_project.key())
            self.log_and_put(user, "Appending a project to a RegisteredUser's my_projects list ")
            self.redirect("/%s/%s" % (user.username, new_project.name))


