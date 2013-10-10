# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
import projects

NOTES_PER_PAGE = 5   # Number of notes displayed in a single page while viewing a notebook. Perhaps later this will be user-customizable.

###########################
##   Datastore Objects   ##
###########################

# Notebooks have a Project as parent.
class Notebooks(ndb.Model):
    owner = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def get_number_of_notes(self):
        return NotebookNotes.query(ancestor = self.key).count()

# Each note should be a child of a Notebook.
class NotebookNotes(ndb.Model):
    title = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)

    def get_number_of_comments(self):
        return NoteComments.query(ancestor = self.key).count()


# Each comment should be a child of a NotebookNote
class NoteComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)


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

    def get_note(self, notebook, note_id, log_message = ''):
        self.log_read(NotebookNotes, log_message)
        return NotebookNotes.get_by_id(int(note_id), parent = notebook.key)

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
        if user:
            for n in notebooks:
                if n.owner == user.key:
                    my_notebooks.append(n)
                else:
                    other_notebooks.append(n)
        self.render("notebooks_list.html", project = project, user = user, visitor_p = (user and project.user_is_author(user)),
                    notebooks = notebooks, my_notebooks = my_notebooks, other_notebooks = other_notebooks)


class NewNotebookPage(NotebookPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = False if project.user_is_author(user) else True
        kw = {"title" : "New notebook",
              "name_placeholder" : "Title of the new notebook",
              "content_placeholder" : "Description of the new notebook",
              "submit_button_text" : "Create notebook",
              "cancel_url" : "/%s/notebooks" % project.key.integer_id(),
              "breadcrumb" : '<li class="active">Notebooks</li>',
              "markdown_p" : True,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not an author in this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        error_message = ''
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            error_message = "You are not an author in this project. "
        n_name = self.request.get("name")
        n_description = self.request.get("content")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for your new notebook. "
        if not n_description:
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if have_error:
            kw = {"title" : "New notebook",
                  "name_placeholder" : "Title of the new notebook",
                  "content_placeholder" : "Description of the new notebook",
                  "submit_button_text" : "Create notebook",
                  "cancel_url" : "/%s/notebooks" % project.key.integer_id(),
                  "breadcrumb" : '<li class="active">Notebooks</li>',
                  "markdown_p" : True,
                  "name_value" : n_name,
                  "content_value" : n_description,
                  "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<p class="text-danger">You are not an author in this project.</p>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_notebook = Notebooks(owner = user.key, 
                                     name = n_name, 
                                     description = n_description, 
                                     parent  = project.key)
            self.put_and_report(user, new_notebook, [project])
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
        page = self.request.get("page")
        try:
            page = int(page)
        except ValueError:
            page = 0
        notes, next_page_cursor, more_p = self.get_notes_list(notebook, page)
        self.render("notebook_main.html", project = project, notebook = notebook, 
                    notes = notes, page = page, more_p = more_p,
                    user_is_owner_p = True if (user and notebook.owner == user.key) else False,
                    owner = notebook.owner.get())


class NewNotePage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + "/new_note"
            self.redirect("/login?goback=%s" % goback)
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
        visitor_p = False if notebook.owner.get().key == user.key else True
        parent_url = "/%s/notebooks" % project.key.integer_id()
        kw = {"title" : "New note",
              "name_placeholder" : "Title of the new note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Create note",
              "cancel_url" : "%s/%s" % (parent_url, nbid),
              "markdown_p" : True,
              "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>' % (parent_url, notebook.name),
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/notebooks/' + nbname + '/new_note'
            self.redirect("/login?goback=%s" % goback)
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
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        n_title = self.request.get("name")
        n_content = self.request.get("content")
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
        if not n_title:
            have_error = True
            error_message = "Please provide a title for this note. "
        if not n_content:
            have_error = True
            error_message += "You need to write some content before saving this note. "
        if have_error:
            parent_url = "/%s/notebooks" % (project.key.integer_id())
            kw = {"title" : "New note",
                  "name_placeholder" : "Title of the new note",
                  "content_placeholder" : "Content of the note",
                  "submit_button_text" : "Create note",
                  "cancel_url" : "%s/%s" % (parent_url ,notebook.key.integer_id()),
                  "markdown_p" : True,
                  "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>' % (parent_url, notebook.name),
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_note = NotebookNotes(title = n_title, content = n_content, parent = notebook.key)
            self.put_and_report(user, new_note, [project, notebook])
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, new_note.key.integer_id()))


class NotePage(NotebookPage):
    def get(self, projectid, nbid, note_id):
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
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        comments = self.get_comments_list(note)
        visitor_p = True if not (user and project.user_is_author(user)) else False
        self.render("notebook_note.html", project = project, user = user,visitor_p = visitor_p,
                    notebook = notebook, note = note, comments = comments, new_comment = self.request.get("new_comment"),
                    user_is_owner_p = (user and notebook.owner == user.key))

    def post(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/' + note_id
            self.redirect("/login?goback=%s" % goback)
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
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        have_error = False
        error_message = ''
        visitor_p = not project.user_is_author(user)
        if visitor_p:
            have_error = True
            error_message = "You are not an author in this project."
        comment = self.request.get("comment")
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = NoteComments(author = user.key, comment = comment, parent = note.key)
            self.put_and_report(user, new_comment, [project, notebook])
            comment = ''
        comments = self.get_comments_list(note)
        self.render("notebook_note.html", project = project, visitor_p = visitor_p,
                    notebook = notebook, note = note, comments = comments, 
                    comment = comment, error_message = error_message,
                    user_is_owner_p = True if (user and notebook.owner == user.key) else False)


class EditNotebookPage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/edit'
            self.redirect("/login?goback=%s" % goback)
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
        visitor_p = False if notebook.owner.get().key == user.key else True
        nbs_url = "/%s/notebooks" % projectid
        kw = {"title" : "Editing notebook <br/> <small>%s</small>" % notebook.name,
              "name_placeholder" : "Title of the notebook",
              "content_placeholder" : "Description of the notebook",
              "submit_button_text" : "Save Changes",
              "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
              "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>' 
              % (nbs_url, notebook.name),
              "name_value" : notebook.name,
              "content_value" : notebook.description,
              "markdown_p" : True,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbname + '/edit'
            self.redirect("/login?goback=%s" % goback)
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
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
        n_name = self.request.get("name")
        n_description = self.request.get("content")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for the notebook. "
        if (not n_description) or (len(n_description.strip()) == 0):
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if have_error:
            nbs_url = "/%s/notebooks" % (projectid)
            kw = {"title" : "Editing notebook <br/><small>%s</small>" % notebook.name,
                  "name_placeholder" : "Title of the notebook",
                  "content_placeholder" : "Description of the notebook",
                  "submit_button_text" : "Save Changes",
                  "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
                  "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li class="active">%s</li>'
                  % (nbs_url, notebook.name),
                  "name_value" : n_name,
                  "content_value" : n_description,
                  "error_message" : error_message,
                  "markdown_p" : True,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            notebook.name = n_name
            notebook.description = n_description
            self.log_and_put(notebook)
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))


class EditNotePage(NotebookPage):
    def get(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + "/notebooks/" + nbid + '/' + note_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
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
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        visitor_p = False if notebook.owner.get().key == user.key else True
        nbs_url = "/%s/notebooks" % projectid
        nb_url = nbs_url + "/" + nbid
        note_url = nb_url + "/" + note_id
        kw = {"title" : "Edit note",
              "name_placeholder" : "Title of the note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Save changes",
              "markdown_p" : True,
              "cancel_url" : note_url,
              "breadcrumb" : '<li><a href="%s">Notebooks</a></li><li><a href="%s">%s</a></li><li class="active">%s</li>'
              % (nbs_url, nb_url, notebook.name, note.title),
              "name_value" : note.title, "content_value" : note.content,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/' + note_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
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
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
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
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<p class="text-danger">You are not the owner of this notebook.</p>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            if (note.title != n_title) or (note.content != n_content):
                note.title = n_title
                note.content = n_content
                self.log_and_put(note)
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, note_id))

