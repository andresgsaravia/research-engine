# notebooks.py
# All related to Notebooks and Notes inside a project.

from google.appengine.ext import ndb
import generic, projects
import logging

NOTES_PER_PAGE = 5   # Number of notes displayed in a single page while viewing a notebook. Perhaps later this will be user-customizable.

###########################
##   Datastore Objects   ##
###########################

# Notebooks have a Project as parent.
class Notebooks(ndb.Model):
    owner = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    shared_p = ndb.BooleanProperty(default = False)   # If true, all users can make notes in it and "owner" is meaningless
    # For an open notebook it's one of ONS-ACI, ONS-ACD, ONS-SCI, ONS-SCD according in its (A)ll or (S)elected content and (I)mmediately or (D)elayed. 
    # Another option is "CNS" for closed notebooks.
    claims = ndb.StringProperty(required = True, default = 'ONS-ACI')

    def get_number_of_notes(self):
        return NotebookNotes.query(ancestor = self.key).count()

    def is_open_p(self):
        return not self.claims == "CNS"

    def claims_logo(self, size = ""):         # size should be "", "icons" or "small"
        if not self.is_open_p(): return ""
        url = "/static/ONS/" + self.claims
        if size: url += "-" + size
        url += ".png"
        return url

    def claims_text(self):
        if not self.is_open_p(): return ""
        text = "This is an open notebook. "
        if self.claims[4] == "A":
            text += "All relevant content is reported here "
        else:
            text += "Only some part of the relevant content is reported here "
        if self.claims[6] == "I":
            text += "in as close to real time as possible."
        else:
            text += "after a significant delay."
        return text
        


# Each note should be a child of a Notebook.
class NotebookNotes(ndb.Model):
    title = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = False) # This is required for shared notebooks, otherwise it can be inferred from its parent.

    def get_number_of_comments(self):
        return NoteComments.query(ancestor = self.key).count()

    def is_open_p(self):
        return self.key.parent().get().is_open_p()

    def get_author(self):
        if self.author:
            return self.author.get()
        else:
            return self.key.parent().get().owner.get()

    def editable_p(self, user):
        author = self.get_author()
        notebook = self.key.parent().get()
        return user and (user.key == author.key)

        
# Each comment should be a child of a NotebookNote
class NoteComments(ndb.Model):
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def is_open_p(self):
        return self.key.parent().get().is_open_p()


######################
##   Web Handlers   ##
######################

class NotebookPage(projects.ProjectPage):
    def get_notebooks_list(self, project):
        self.log_read(Notebooks, "Fetching all the notebooks for a project")
        return Notebooks.query(ancestor = project.key).order(-Notebooks.last_updated).fetch()

    def get_notebook(self, project, nbid, log_message = ''):
        self.log_read(Notebooks, log_message)
        return Notebooks.get_by_id(int(nbid), parent = project.key)

    def get_notes_list(self, notebook, page = 0, log_message = ''):
        assert type(page) == int
        self.log_read(NotebookNotes, "Fetching a page with %s results. %s" % (NOTES_PER_PAGE, log_message))
        return NotebookNotes.query(ancestor = notebook.key).order(-NotebookNotes.date).fetch_page(NOTES_PER_PAGE, offset = NOTES_PER_PAGE * page)

    def get_note(self, notebook, noteid, log_message = ''):
        self.log_read(NotebookNotes, log_message)
        return NotebookNotes.get_by_id(int(noteid), parent = notebook.key)

    def get_comments_list(self, note):
        self.log_read(NoteComments, "Fetching all the comments for a note in a notebook. ")
        return  NoteComments.query(ancestor = note.key).order(NoteComments.date).fetch()

    def render(*a, **kw):
        projects.ProjectPage.render(notebooks_tab_class = "active", *a, **kw)


class NotebooksListPage(NotebookPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebooks = self.get_notebooks_list(project)
        my_notebooks = []
        other_notebooks = []
        shared_notebooks = []
        if user:
            for n in notebooks:
                if n.shared_p:
                    shared_notebooks.append(n)
                elif n.owner == user.key:
                    my_notebooks.append(n)
                else:
                    other_notebooks.append(n)
        self.render("notebooks_list.html", project = project, user = user, notebooks = notebooks, 
                    my_notebooks = my_notebooks, other_notebooks = other_notebooks, shared_notebooks = shared_notebooks)


class NewNotebookPage(NotebookPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/new" % projectid)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/notebooks" % projectid)
            return
        self.render("notebook_new.html", project = project, action = "New", button_text = "Create notebook",
                    n_claims = "ONS-ACI" if project.default_open_p else "CNS")

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/new" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/notebooks" % projectid)
            return
        have_error = False
        kw = {"error_message" : '',
              "n_name" : self.request.get("name"),
              "n_description" : self.request.get("description"),
              "n_claims" : self.request.get("claims"),
              "shared_p" : self.request.get("shared_p") == "True"}
        if not kw["n_name"]:
            have_error = True
            kw["error_message"] = "Provide a name for your new notebook. "
            kw["nClass"] = "has-error"
        if not kw["n_description"]:
            have_error = True
            kw["error_message"] += "Provide a description of this notebook. "
            kw["dClass"] = "has-error"
        if not kw["n_claims"] in ["ONS-ACI","ONS-ACD","ONS-SCI","ONS-SCD","CNS"]:
            have_error = True
            error_message += "There was an error procesing your request, please try again."
        if have_error:
            self.render("notebook_new.html", project = project, action = "New", button_text = "Create notebook", **kw)
        else:
            new_notebook = Notebooks(owner = user.key, 
                                     name = kw["n_name"], 
                                     description = kw["n_description"], 
                                     parent  = project.key,
                                     claims = kw["n_claims"],
                                     shared_p = kw["shared_p"])
            self.put_and_report(new_notebook, user, project)
            self.redirect("/%s/notebooks/%s" % (project.key.integer_id(), new_notebook.key.id()))


class NotebookMainPage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (notebook.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        kw = {"page" : self.request.get("page")}
        try:
            kw["page"] = int(kw["page"])
        except ValueError:
            kw["page"] = 0
        kw["notes"], kw["next_page_cursor"], kw["more_p"] = self.get_notes_list(notebook, kw["page"])
        self.render("notebook_main.html", project = project, notebook = notebook, 
                    writable_p = user and (notebook.owner == user.key or notebook.shared_p),
                    owner = notebook.owner.get(), **kw)


class NewNotePage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/new_note" % (projectid, nbid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (user.key == notebook.owner or notebook.shared_p):
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))
            return
        parent_url = "/%s/notebooks" % project.key.integer_id()
        kw = {"title" : "New note",
              "subtitle" : notebook.name,
              "name_placeholder" : "Title of the new note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Create note",
              "cancel_url" : "%s/%s" % (parent_url, nbid),
              "markdown_p" : True,
              "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>' % (parent_url, notebook.name)}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/new_note" % (projectid, nbid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (user.key == notebook.owner or notebook.shared_p):
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))
            return
        have_error = False
        error_message = ''
        n_title = self.request.get("name")
        n_content = self.request.get("content")
        if not n_title:
            have_error = True
            error_message = "Please provide a title for this note. "
        if not n_content:
            have_error = True
            error_message += "You need to write some content before saving this note. "
        if have_error:
            parent_url = "/%s/notebooks" % (project.key.integer_id())
            kw = {"title" : "New note",
                  "subtitle" : notebook.name,
                  "name_placeholder" : "Title of the new note",
                  "content_placeholder" : "Content of the note",
                  "submit_button_text" : "Create note",
                  "cancel_url" : "%s/%s" % (parent_url ,notebook.key.integer_id()),
                  "markdown_p" : True,
                  "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>' % (parent_url, notebook.name),
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_note = NotebookNotes(title = n_title, content = n_content, parent = notebook.key, author = user.key)
            self.put_and_report(new_note, user, project, notebook)
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, new_note.key.integer_id()))


class NotePage(NotebookPage):
    def get(self, projectid, nbid, noteid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, noteid)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % noteid)
            return
        if not (notebook.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        kw = {"comments" : self.get_comments_list(note)}
        kw["visitor_p"] = not (user and project.user_is_author(user))
        self.render("notebook_note.html", project = project, user = user,
                    notebook = notebook, note = note, new_comment = self.request.get("new_comment"),
                    note_editable_p = note.editable_p(user), **kw)

    def post(self, projectid, nbid, noteid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, noteid)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % noteid)
            return
        have_error = False
        kw = {}
        comment = self.request.get("comment")
        if not comment:
            have_error = True
            kw["error_message"] = "You can't submit an empty comment. "
        if not have_error:
            comment_id = self.request.get("comment_id")   # If this is present, we are editing a comment, otherwise it's a new comment
            if comment_id:
                # Edit comment
                c = NoteComments.get_by_id(int(comment_id), parent = note.key)
                c.comment = comment
                self.log_and_put(c)
            else:
                # New comment
                new_comment = NoteComments(author = user.key, comment = comment, parent = note.key)
                self.put_and_report(new_comment, user, project, notebook)
        kw["comments"] = self.get_comments_list(note)
        self.render("notebook_note.html", project = project,
                    notebook = notebook, note = note, comment = '',
                    note_editable_p = user and ((not notebook.shared_p and notebook.owner == user.key) 
                                                or (notebook.shared_p and note.author == user.key)), **kw)


class EditNotebookPage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/edit" % (projectid, nbid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (notebook.owner.get().key == user.key or (notebook.shared_p and project.user_is_author(user))):
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))
            return
        kw = {"action" : "Edit",
              "button_text" : "Save Changes",
              "n_name" : notebook.name,
              "n_description" : notebook.description,
              "n_claims" : notebook.claims,
              "shared_p" : notebook.shared_p}
        self.render("notebook_new.html", project = project, notebook = notebook, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/edit" % (projectid, nbid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (notebook.owner.get().key == user.key or (notebook.shared_p and project.user_is_author(user))):
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))
            return
        have_error = False
        error_message = ''
        n_name = self.request.get("name")
        n_description = self.request.get("description")
        n_claims = self.request.get("claims")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for the notebook. "
        if (not n_description) or (len(n_description.strip()) == 0):
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if not n_claims in ["ONS-ACI","ONS-ACD","ONS-SCI","ONS-SCD","CNS"]:
            have_error = True
            error_message = "There was an error with your request, please try again. "
        if have_error:
            nbs_url = "/%s/notebooks" % (projectid)
            kw = {"action" : "Edit",
                  "button_text" : "Save Changes",
                  "n_name" : n_name,
                  "n_description" : n_description,
                  "n_claims" : n_claims,
                  "error_message" : error_message}
            self.render("notebook_new.html", project = project, **kw)
        else:
            notebook.name = n_name
            notebook.description = n_description
            notebook.claims = n_claims
            self.log_and_put(notebook)
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))


class EditNotePage(NotebookPage):
    def get(self, projectid, nbid, noteid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/%s/edit" % (projectid, nbid, noteid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, noteid)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % noteid)
            return
        note_editable_p = user and (notebook.owner == user.key or (notebook.shared_p and note.author == user.key))
        if not note_editable_p:
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        nbs_url = "/%s/notebooks" % projectid
        nb_url = nbs_url + "/" + nbid
        note_url = nb_url + "/" + noteid
        kw = {"title" : "Edit note",
              "name_placeholder" : "Title of the note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Save changes",
              "markdown_p" : True,
              "cancel_url" : note_url,
              "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li><a href="%s">%s</a></li><li class="active">%s</li>'
              % (nbs_url, nb_url, notebook.name, note.title),
              "name_value" : note.title, "content_value" : note.content}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid, noteid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/%s/edit" % (projectid, nbid, noteid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, noteid)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % noteid)
            return
        note_editable_p = user and (notebook.owner == user.key or (notebook.shared_p and note.author == user.key))
        if not note_editable_p:
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        have_error = False
        error_message = ''
        n_title = self.request.get("name")
        n_content = self.request.get("content")
        if not n_title:
            have_error = True
            error_message = "Please provide a title for this note. "
        if not n_content:
            have_error = True
            error_message += "You need to write some content before saving this note. "
        if have_error:
            kw = {"title" : "New note",
                  "name_placeholder" : "Title of the new note",
                  "content_placeholder" : "Content of the note",
                  "submit_button_text" : "Create note",
                  "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
                  "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li><a href="%s">%s</a></li><li class="active">%s</li>' 
                  % (nbs_url, nb_url, notebook.name, note.title),
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message}
            self.render("project_form_2.html", project = project, **kw)
        else:
            if (note.title != n_title) or (note.content != n_content):
                note.title = n_title
                note.content = n_content
                self.log_and_put(note)
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, noteid))

class NotebookUtils(NotebookPage):
    def index(self, projectid, nbid):
        "Returns an HTML index for all the notes in this notebook"
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        if not (notebook.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        notes = NotebookNotes.query(ancestor = notebook.key).order(-NotebookNotes.date).fetch()
        self.render("notebook_index.html", project = project, notebook = notebook, notes = notes)
