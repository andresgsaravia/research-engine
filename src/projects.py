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
        self.render("projects.html", user = user, projects = projects, handler = self)


class NewProjectPage(GenericPage):
    # Template variables (form_text_textarea.html)
    kw = {"fancy_textarea_p" : False,
          "page_title" : "New Project",
          "title" : "New Project",
          "subtitle" : '',
          "action" : "/projects/new",
          "text_name" : "p_name",
          "text_placeholder" : "Name of the project",
          "textarea_name" : "p_description",
          "textarea_placeholder" : "Description of the project",
          "submit_value" : "Create new project",
          "cancel_url" : "/projects"}

    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return              
        self.render("form_text_textarea.html", **self.kw)

    def post(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        have_error = False
        p_name = self.request.get("p_name")
        p_description = self.request.get("p_description")
        error = ''
        if not p_name:
            have_error = True
            error += "Please provide a name for your new project. "
        if not p_description:
            have_error = True
            error += "Please provide a brief description of your new project. "
        if have_error:
            self.render("form_text_textarea.html", 
                        error = error, text_value = p_name, textarea_value = p_description, **self.kw)
        else:
            project = Projects(name = p_name, description = p_description, 
                               authors = [user.key()], references = [], notebooks = [])
            self.log_and_put(project, "Creating a new Project. ")
            user.my_projects.append(project.key())
            self.log_and_put(user, "Appending a new project to my_projects of a RegisteredUser. ")
            self.redirect("/projects/project/%s" % project.key())
        
# Needs to handle the case in which project_key is invalid
class ProjectPage(GenericPage):
    def get(self, project_key):
        project = self.get_item_from_key_str(project_key)
        kw = {"project_key" : project_key, 
              "project"     : project, 
              "ref_list"    : []}
        for ref_key in project.references:
            kw["ref_list"].append(self.get_item_from_key(ref_key))
        kw["ref_list"].reverse()
        kw["len_ref_list"] = len(kw["ref_list"])
        # Notebooks
        notebooks = Notebooks.all().ancestor(project).order('-last_updated')
        kw["nb_list"] = []
        for nb in notebooks.run():
            self.log_read(Notebooks)
            kw["nb_list"].append(nb)
        kw["len_nb_list"] = len(kw["nb_list"])
        # Collaborative Writings
        kw["wrt_list"] = []
        writings = CollaborativeWritings.all().ancestor(project).order("last_updated")
        for wr in writings.run():
            self.log_read(CollaborativeWritings)
            kw["wrt_list"].append(wr)
        kw["len_wrt_list"] = len(kw["wrt_list"])
        kw["authors"] = project.list_of_authors(self)
        self.render("project.html", **kw)

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
            self.log_and_put(project, "New collaborator in a Project. ")
            new_collaborator.my_projects.append(project.key())
            self.log_and_put(new_collaborator, "Updating my_projects property. ")
            self.redirect("/projects/project/%s" % project_key)
        

class EditProjectPage(GenericPage):
    # Template variables (form_text_textarea.html)
    kw = {"fancy_textarea_p" : False,
          "page_title" : "Edit Project",
          "title" : "Edit Project",
          "subtitle" : '',
          "text_name" : "p_name",
          "text_placeholder" : "Name of the project",
          "textarea_name" : "p_description",
          "textarea_placeholder" : "Description of the project",
          "submit_value" : "Save changes"}

    def get(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if project:
            if project.user_is_author(user):
                t_kw = self.kw
                t_kw["action"] = "/projects/project/edit/%s" % project_key
                t_kw["text_value"] = project.name
                t_kw["textarea_value"] = project.description
                t_kw["cancel_url"] = "/projects/project/%s" % project_key
                self.render("form_text_textarea.html", **t_kw)
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
        project = self.get_item_from_key_str(project_key)
        have_error = False
        error = ''
        if project:
            if project.user_is_author(user):
                project_name = self.request.get("p_name")
                description = self.request.get("p_description")
                if not project_name:
                    have_error = True
                    error += "You must provide a name for the project. "
                if not description:
                    have_error = True
                    error += "You must provide a description for the project. "
                if have_error:
                    t_kw = self.kw
                    t_kw["action"] = "/projects/project/edit/%s" % project_key
                    t_kw["text_value"] = project_name
                    t_kw["textarea_value"] = description
                    t_kw["cancel_url"] = "/projects/project/%s" % project_key
                    self.render("form_text_textarea.html", error = error, **t_kw)
                else:
                    if (project.name != project_name) or (project.description != description):
                        project.name = project_name
                        project.description = description
                        self.log_and_put(project, "Updating information. ")
                    self.redirect("/projects/project/%s" % project.key())
            else:
                self.redirect("/projects/project/%s" % project_key)
        else:
            logging.debug("Attempting to fetch a non-existing edit-project page with key %s" % project_key)
            self.error(404)


class RecentActivityPage(GenericPage):
    def get(self):
        self.render("under_construction.html")



