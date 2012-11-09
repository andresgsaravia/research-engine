# projects.py
# For creating, managing and updating projects.

from generic import *
from references import *

SHORT_DESCRIPTION_LENGTH = 150

##########################
##   Helper Functions   ##
##########################


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


# Notebooks have a Project as parent.
class Notebooks(db.Model):
    owner = db.ReferenceProperty(required = True)
    name = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    started = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)

    def short_render(self, project_key):
        last_note_date = self.last_updated.strftime("%d-%b-%Y")
        owner_name = self.owner.username
        return render_str("notebook_short.html", notebook = self, project_key = project_key,
                          last_note_date = last_note_date, owner_name = owner_name)

    def short_description(self):
        if len(self.description) < SHORT_DESCRIPTION_LENGTH:
            return self.description
        else:
            return self.description[0:SHORT_DESCRIPTION_LENGTH - 3] + "..."


# Each note should be a child of a Projects instance.
class NotebookNotes(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)


######################
##   Web Handlers   ##
######################

class MainPage(GenericPage):
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


##   Projects   ##

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
        project = self.get_item_from_key(db.Key(project_key))
        ref_list = []
        for ref_key in project.references:
            ref_list.append(self.get_item_from_key(ref_key))
        ref_list.reverse()
        notebooks = Notebooks.all().ancestor(project).order('last_updated')
        nb_list = []
        for nb in notebooks.run():
            nb_list.append(nb)
        nb_list.reverse()
        self.render("project.html", project = project, project_key = project_key, 
                    ref_list = ref_list, len_ref_list = len(ref_list),
                    nb_list = nb_list, len_nb_list = len(nb_list))
        

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


##   Notebooks   ##

class NewNotebookPage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user: 
            self.redirect("/login")
            return
        self.render("notebook_new.html", project_key = project_key)

    def post(self, project_key):
        user = self.get_user()
        project = db.Query().filter("__key__ =", db.Key(project_key)).get()
#        project = self.get_item_form_key(db.Key(project_key)) # Why is this not working?
        if not user:
            self.redirect("/login")
            return
        n_name = self.request.get("n_name")
        n_description = self.request.get("n_description")
        have_error = False
        error = ''
        if not n_name:
            have_error = True
            error += 'You must provide a name for your new notebook. '
        if not n_description:
            have_error = True
            error += 'Please provide a brief description of your new notebook. '
        if not (user.key() in project.authors):
            have_error = True
            error += "You can't add a notebook to this project since you are not one of its authors. "
        if have_error:
            self.render("notebook_new.html", n_name = n_name, n_description = n_description, error = error)
        else:
            new_notebook = Notebooks(owner = user.key(), name = n_name, description = n_description, 
                                     parent  = db.Key(project_key))
            logging.debug("DB WRITE: Handler NewNotebookPage is creating a new instance of Notebooks.")
            new_notebook.put()
            user.my_notebooks.append(new_notebook.key())
            logging.debug("DB WRITE: Handler NewNotebookPage is appending a new notebook to a RegiteredUser's my_notebooks list.")
            user.put()
            logging.debug("DB WRITE: Handler NewNotebookPage is updating a project's last_updated property.")
            project.put()
            self.redirect("/projects/project/%s/nb/%s" % (project_key, new_notebook.key()))


class NotebookPage(GenericPage):
    def get(self, project_key, notebook_key):
        notebook = self.get_item_from_key(db.Key(notebook_key))
        if not notebook:
            self.error(404)
            return
        params = {'project_key' : project_key, 'notebook' : notebook}
        logging.debug("DB READ: Handler NotebookPage is getting all the notes for a notebook.")
        params["notes"] = []
        for note in NotebookNotes.all().ancestor(notebook).order("-date").run():
            params["notes"].append(note)
        self.render("notebook.html", **params)


class EditNotebookPage(GenericPage):
    def get(self, project_key, notebook_key):
        notebook = self.get_item_from_key_str(notebook_key)
        self.render("notebook_edit.html", notebook = notebook, project_key = project_key, notebook_key = notebook_key)

    def post(self, project_key, notebook_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebook = self.get_item_from_key_str(notebook_key)
        if not notebook:
            self.error(404)
            return
        nb_name = self.request.get("nb_name")
        nb_description = self.request.get("nb_description")
        params = {"project_key" : project_key, "notebook_key" : notebook_key, "notebook" : notebook,
                  "nb_name" : nb_name, "nb_description" : nb_description, "error" : ""}
        have_error = False
        if not nb_name:
            have_error = True
            params["error"] += "Please provide a name for your notebook. "
        if not nb_description:
            have_error = True
            params["error"] += "Please provide  a description for your notebook. "
        if not notebook.owner == user.key():
            have_error = True
            params["error"] = "You are not the owner of this notebook. "
        if have_error:
            self.render("notebook_edit.html", **params)
        else:
            notebook.name = nb_name
            notebook.description = nb_description
            logging.debug("DB WRITE: Handler EditNotebookPage is editing a notebook's details.")
            notebook.put()
            self.redirect("/projects/project/%s/nb/%s" % (project_key, notebook_key))


class NewNotePage(GenericPage):
    def get(self, project_key, notebook_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebook = self.get_item_from_key_str(notebook_key)
        error = ''
        if not notebook.owner.key() == user.key():
            error = "You are not the owner of this notebook; you can not add a new note to it."
        self.render("notebook_new_note.html", notebook = notebook, error = error)

    def post(self, project_key, notebook_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        notebook = self.get_item_from_key_str(notebook_key)
        error = ""
        title = self.request.get("title")
        content = self.request.get("content")
        have_error = False
        if not notebook.owner.key() == user.key():
            have_error = True
            error = "You are not the owner of this notebook; you can not add a new note to it."
        if not title:
            have_error = True
            error += "Please provide a title for your note. "
        if not content:
            have_error = True
            error += "Please provide a content for your note. "
        if have_error:
            self.render("notebook_new_note.html", notebook = notebook, error = error, 
                        title = title, content = content)
        else:
            new_note = NotebookNotes(title = title, content = content, parent = notebook)
            logging.debug("DB WRITE: Handler NewNotePage is writing a new instance of NotebookNotes.")
            new_note.put()
            logging.debug("DB WRITE: Handler NewNotePage is updating a Notebook's last_updated property.")
            notebook.put()
            logging.debug("DB WRITE: Handler NewNotePage is updating a Project's last_updated property.")
            project.put()
            self.redirect("/projects/project/%s/nb/note/%s" % (project_key, new_note.key()))


class NotePage(GenericPage):
    def get(self, project_key, note_key):
        self.render("under_construction.html")


##   References   ##

class NewReferencePage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        self.render("project_new_reference.html")

    def post(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key(db.Key(project_key))
        kind_of_reference = self.request.get("kind_of_reference")
        identifier = self.request.get("identifier")
        try:
            reference = get_add_reference(kind_of_reference, identifier)
            if not (reference.key() in project.references):
                project.references.append(reference.key())
                logging.debug("DB WRITE: Handler NewReferencePage is adding a reference to a project.")
                project.put()
            self.redirect("/projects/project/%s/ref/%s" % (project_key, reference.key()))
            

        except:
            self.render("project_new_reference.html", error = "Could not retrieve reference")


class ReferencePage(GenericPage):
    def get(self, project_key, reference_key):
        reference = self.get_item_from_key(db.Key(reference_key))
        self.render("reference.html", reference = reference,
                    project_key = project_key, reference_key = reference_key)


class EditReferencePage(GenericPage):
    def get(self, project_key, reference_key):
        reference = self.get_item_from_key(db.Key(reference_key))
        if not reference: 
            logging.warning("Attempted to fetch a non-existing reference's page; key :1", reference_key)
            self.error(404)
        else:
            self.render("reference_edit.html", reference = reference, reference_key = reference_key,
                        project_key = project_key)

    def post(self, project_key, reference_key):
        username = self.get_username()
        if not username: self.redirect("/login")
        params = {}
        params["project_key"] = project_key
        params["reference_key"] = reference_key
        reference = self.get_item_from_key(db.Key(reference_key))
        if not reference:
            logging.warning("Attempted to fetch a non-existing reference's page; key :1", reference_key)
            self.error(404)
        else:
            kind = reference.kind()
            have_error = False
            params["error"] = ''

            if kind == "arXiv":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get("authors_string")
                params["date"] = self.request.get("date")
                params["abstract"]= self.request.get("abstract")
                params["link"] = self.request.get("link")
                if params["title"]: reference.title = nice_bs(params["title"])
                if params["authors_string"]:
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params["date"]:
                    try:
                        reference.date = datetime.datetime.strptime(nice_bs(params["date"]), "%Y-%m-%d")
                    except ValueError:
                        have_error = True
                        params["error"] += "Please check the date is correct. "
                if params["abstract"]: reference.abstract = nice_bs(params["abstract"])
                if params["link"]: 
                    try:
                        reference.link = nice_bs(params["link"])
                    except db.BadValueError:
                        have_error = True
                        params["error"] += "Please check the Link value is a valid URL. "

            elif kind == "PublishedArticles":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get("authors_string")
                params["year"] = self.request.get("year")
                params["issue"] = self.request.get("issue")
                params["volume"] = self.request.get("volume")
                params["page"] = self.request.get("page")
                params["abstract"] = self.request.get("abstract")
                params["link"] = self.request.get("link")
                if params["title"]: reference.title = nice_bs(params["title"])
                if params["authors_string"]: 
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params["year"]: 
                    try:
                        reference.year = int(nice_bs(params["year"]))
                    except ValueError:
                        have_error = True
                        params["error"] += "Please write Year as a single positive integer."
                if params["issue"]: reference.issue = nice_bs(params["issue"])
                if params["volume"]: reference.volume = nice_bs(params["volume"])
                if params["page"]: reference.page = nice_bs(params["page"])
                if params["abstract"]: reference.abstract = nice_bs(params["abstract"])
                if params["link"]: 
                    try:
                        reference.link = nice_bs(params["link"])
                    except db.BadValueError:
                        have_error = True
                        params["error"] += "Please check the link value is a valid URL. "

            elif kind == "WebPage":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get('authors_string')
                params["summary"] = self.request.get('summary')
                if params['title']: reference.title = nice_bs(params['title'])
                if params["authors_string"]:
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params['summary']: reference.summary = nice_bs(params['summary'])
            else:
                logging.error("Wrong reference species: %s" % species)
                assert False

            if have_error:
                self.render("reference_edit.html", reference = reference, **params)
            else:
                logging.debug("DB WRITE: Updating %s reference metadata." % kind)
                reference.put()
                self.redirect("/projects/project/%s/ref/%s" % (project_key, reference_key))

class RecentActivityPage(GenericPage):
    def get(self):
        self.render("under_construction.html")
