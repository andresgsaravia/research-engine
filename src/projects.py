# projects.py
# For creating, managing and updating projects.

from generic import *
from references import *
from notebooks import *
from collab_writing import *

SHORT_DESCRIPTION_LENGTH = 150


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
    
    def list_of_authors(self):
        authors_list = []
        for author_key in self.authors:
            logging.debug("DB READ: Getting an author from a project's list of authors.")
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
            return self.description[0:147] + "..."

    def short_render(self):
        return render_str("project_short.html", project = self)

    def full_render(self):
        p_description = self.description.replace("\n", "<br/>")
        return render_str("project_full.html", p_description = p_description, project = self)


######################
##   Web Handlers   ##
######################

class ProjectsPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        projects = []
        for project_key in user.my_projects:
            project = self.get_item_from_key(project_key)
            if project: projects.append(project)
        projects.sort(key=lambda p: p.last_updated, reverse=True)
        self.render("projects_main.html", user = user, projects = projects)


class NewProjectPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        self.render("project_new.html")

    def post(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        have_error = False
        params = {}
        params["p_name"] = self.request.get("p_name")
        params["p_description"] = self.request.get("p_description")
        params["error"] = ''
        if not params["p_name"]:
            have_error = True
            params["error"] += "Please provide a name for your new project. "
        if not params["p_description"]:
            have_error = True
            params["error"] += "Please provide a brief description of your new project. "
        if have_error:
            self.render("project_new.html", **params)
        else:
            project = Projects(name = params["p_name"], description = params["p_description"], 
                               authors = [user.key()], references = [], notebooks = [])
            logging.debug("DB WRITE: Adding a new project to Projects.")
            project.put()
            user.my_projects.append(project.key())
            logging.debug("DB WRITE: Appending a new project to my_projects of a RegisteredUsers entry.")
            user.put()
            self.redirect("/projects/project/%s" % project.key())
        
# Needs to handle the case in which project_key is invalid
class ProjectPage(GenericPage):
    def get(self, project_key):
        params = {"project_key" : project_key}
        project = self.get_item_from_key_str(project_key)
        params["project"] = project
        # References
        params["ref_list"] = []
        for ref_key in project.references:
            params["ref_list"].append(self.get_item_from_key(ref_key))
        params["ref_list"].reverse()
        params["len_ref_list"] = len(params["ref_list"])
        # Notebooks
        notebooks = Notebooks.all().ancestor(project).order('-last_updated')
        params["nb_list"] = []
        for nb in notebooks.run():
            params["nb_list"].append(nb)
        params["len_nb_list"] = len(params["nb_list"])
        # Collaborative Writings
        params["wrt_list"] = []
        writings = CollaborativeWritings.all().ancestor(project).order("last_updated")
        for wr in writings.run():
            params["wrt_list"].append(wr)
        params["len_wrt_list"] = len(params["wrt_list"])
        self.render("project.html", **params)

    def post(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        if not (user.key() in project.authors):
            self.write("You are not allowed to do that.")
            return
        action = self.request.get("action")
        if action == "add_collaborator":
            new_collaborator = self.get_item_from_key_str(self.request.get("new_collaborator_key"))
            assert new_collaborator     # There souldn't be a way to make this request with a bad key.
            assert not (new_collaborator.key() in project.authors)
            project.authors.append(new_collaborator.key())
            logging.debug("DB WRITE: Handler ProjectPage is adding a new collaborator to a project.")
            project.put()
            logging.debug("DB WRITE: Handler ProjectPage is updting a RegisteredUser's my_projects property.")
            new_collaborator.my_projects.append(project.key())
            new_collaborator.put()
            self.redirect("/projects/project/%s" % project_key)
        

class EditProjectPage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key(db.Key(project_key))
        if project:
            if project.user_is_author(user):
                self.render("project_edit.html", project = project)
            else:
                self.redirect("/projects/project/%s" % project_key)
        else:
            logging.debug("Attempting to fetch a non-existing edit-project page with key %s" % project_key)
            self.error(404)

    def post(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        logging.debug("DB READ: Fetching a project to edit its information from a submitted form.")
        project = db.Query().filter("__key__ =", db.Key(project_key)).get()
        have_error = False
        error = ''
        if project:
            if project.user_is_author(user):
                project_name = self.request.get("project_name")
                description = self.request.get("description")
                if not project_name:
                    have_error = True
                    error += "You must provide a name for the project. "
                if not description:
                    have_error = True
                    error += "You must provide a description for the project. "
                if have_error:
                    self.render("project_edit.html", project = project, error = error)
                else:
                    if (project.name != project_name) or (project.description != description):
                        project.name = project_name
                        project.description = description
                        logging.debug("DB WRITE: Updating a project's information.")
                        project.put()
                    self.redirect("/projects/project/%s" % project.key())


class RecentActivityPage(GenericPage):
    def get(self):
        self.render("under_construction.html")



