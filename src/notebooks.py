# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
import projects

SHORT_DESCRIPTION_LENGTH = 150
NOTEBOOK_NAME_REGEXP = r'^[a-zA-Z0-9\s-]+$'

###########################
##   Datastore Objects   ##
###########################

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


# Each note should be a child of a Notebook.
class NotebookNotes(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)


######################
##   Web Handlers   ##
######################

class NotebooksListPage(GenericPage):
    def get(self, username, project_name):
        user = self.get_user()
        if not user:
            self.redirect('/login')
            return
        p_user = RegisteredUsers.all().filter("username =", username).get()
        if not p_user:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_user):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        notebooks = []
        for n in Notebooks.all().ancestor(project).order("-last_updated").run():
            notebooks.append(n)
        self.render("project_notebooks.html", p_author = p_user, project = project, notebooks = notebooks, n_len = len(notebooks))



class NewNotebookPage(GenericPage):
    def get(self, username, project_name):
        user = self.get_user()
        if not user:
            self.redirec('/login')
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        kw = {"title" : "New notebook",
              "name_placeholder" : "Title of the new notebook",
              "content_placeholder" : "Description of the new notebook",
              "submit_button_text" : "Create notebook",
              "cancel_url" : "/%s/%s/notebooks" % (p_author.username, project.name),
              "more_head" : "<style>.notebooks-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, project_name):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project:
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        n_name = self.request.get("name")
        n_description = self.request.get("content")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for your new notebook. "
        if not n_description:
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if n_name and (not re.match(NOTEBOOK_NAME_REGEXP, n_name)):
            have_error = True
            error_message = "Invalid notebook name. Please use only letters, numbers, spaces and dashes. "
        # Check for duplicate notebook names.
        duplicate_p = Notebooks.all().ancestor(project).filter("name =", n_name.lower().replace(" ", "_")).get()
        if duplicate_p:
            have_error = True
            error_message = "There is a notebook with the same name in this project, please choose a different name."
        if have_error:
            kw = {"title" : "New notebook",
                  "name_placeholder" : "Title of the new notebook",
                  "content_placeholder" : "Description of the new notebook",
                  "submit_button_text" : "Create notebook",
                  "cancel_url" : "/%s/%s/notebooks" % (p_author.username, project.name),
                  "more_head" : "<style>.notebooks-tab {background: white;}</style>",
                  "name_value" : n_name,
                  "content_value" : n_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_notebook = Notebooks(owner = user.key(), 
                                     name = n_name.lower().replace(" ", "_"), 
                                     description = n_description, 
                                     parent  = project.key())
            self.log_and_put(new_notebook)
            user.my_notebooks.append(new_notebook.key())
            self.log_and_put(user, "Updating my_notebooks property. ")
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/notebooks/%s" % (user.username, project.name, new_notebook.name))


###########################################################
#### EVERTTHING BELOW SHOULD BE REVISED AND/OR REMOVED ####
###########################################################



class EditNotebookPage(NewNotebookPage):
    def get(self, project_key, notebook_key):
        self.kw["submit_value"] = "Update notebook"
        notebook = self.get_item_from_key_str(notebook_key)
        project = self.get_item_from_key_str(project_key)
        if (not notebook) or (not project):
            self.error(404)
            self.render("404.html")
            return
        self.render("form_text_textarea.html",
                    subtitle = project.name,
                    cancel_url = "/projects/project/%s/nb/%s"  % (project_key, notebook_key),
                    text_value = notebook.name, textarea_value = notebook.description,
                    **self.kw)

    def post(self, project_key, notebook_key):
        self.kw["submit_value"] = "Update notebook"
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebook = self.get_item_from_key_str(notebook_key)
        if not notebook:
            self.error(404)
            return
        kw = {"project_key"    : project_key, 
              "notebook_key"   : notebook_key, 
              "notebook"       : notebook,
              "nb_name"        : self.request.get("nb_name"),
              "nb_description" : self.request.get("nb_description"),
              "error"          : ""}
        have_error = False
        if not kw["nb_name"]:
            have_error = True
            kw["error"] += "Please provide a name for your notebook. "
        if not kw["nb_description"]:
            have_error = True
            kw["error"] += "Please provide  a description for your notebook. "
        if not notebook.owner.key() == user.key():
            have_error = True
            kw["error"] = "You are not the owner of this notebook. "
        if have_error:
            self.render("notebook_edit.html", **kw)
        else:
            notebook.name = kw["nb_name"]
            notebook.description = kw["nb_description"]
            self.log_and_put(notebook)
            self.redirect("/projects/project/%s/nb/%s" % (project_key, notebook_key))


class NotebookPage(GenericPage):
    def get(self, project_key, notebook_key):
        notebook = self.get_item_from_key(db.Key(notebook_key))
        if not notebook:
            self.error(404)
            return
        kw = {'project_key' : project_key, 'notebook' : notebook, "notes" : []}
        for note in NotebookNotes.all().ancestor(notebook).order("-date").run():
            self.log_read(NotebookNotes)
            kw["notes"].append(note)
        self.render("notebook.html", **kw)


class NewNotePage(GenericPage):
    def get(self, project_key, notebook_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebook = self.get_item_from_key_str(notebook_key)
        error = ''
        if not notebook.owner.key() == user.key():
            error = "You are not the owner of this notebook; you cannot add a new note to it."
        self.render("notebook_new_note.html", notebook = notebook, error = error, project_key = project_key)

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
            self.log_and_put(new_note)
            self.log_and_put(notebook, "Updating last_updated property. ")
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/projects/project/%s/nb/note/%s" % (project_key, new_note.key()))


class NotePage(GenericPage):
    def get(self, project_key, note_key):
        note = self.get_item_from_key_str(note_key)
        self.log_read(Notebooks)
        notebook = note.parent()
        self.render("notebook_note.html", project_key = project_key, note = note, notebook = notebook)


class EditNotePage(GenericPage):
    def get(self, project_key, note_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        note = self.get_item_from_key_str(note_key)
        if not note:
            self.error(404)
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        self.log_read(Notebooks)
        notebook = note.parent()
        assert notebook  # We shouldn't have Notes without Notebooks.
        error = ''
        if not notebook.owner.key() == user.key():
            error = "You are not the owner of this notebook; you will be unable to make changes."
        self.render("note_edit.html", note = note, notebook = notebook, error = error, project_key = project_key)

    def post(self, project_key, note_key):
        user = self.get_user()
        if not user:
            self.redirec("/login")
            return
        action = self.request.get("action")
        assert action
        note = self.get_item_from_key_str(note_key)
        kw = {"note" : note}
        if not note:
            self.error(404)
            return
        kw["project"] = self.get_item_from_key_str(project_key)
        if not kw["project"]:
            self.error(404)
            return
        self.log_read(Notebooks)
        notebook = note.parent()
        assert notebook  # We shouldn't have Notes without Notebooks.
        kw["error"] = ''
        have_error = False
        if action == "edit":
            kw["title"] = self.request.get("title")
            kw["content"] = self.request.get("content")
            if not kw["title"]:
                have_error = True
                kw["error"] += "Please provide a title for the note. "
            if not kw["content"]:
                have_error = True
                kw["content"] += "Please provide a content for the note. "
            if not notebook.owner.key() == user.key():
                have_error = True
                kw["error"] = "You are not the owner of this notebook; you are unable to make changes. "
            if have_error:
                self.render("note_edit.html", **kw)
            else:
                note.title = kw["title"]
                note.content = kw["content"]
                self.log_and_put(note)
                self.redirect("/projects/project/%s/nb/note/%s" % (project_key, note_key))
        elif action == "delete":
            self.log_and_delete(note)
            self.redirect("/projects/project/%s/nb/%s" % (project_key, notebook.key()))


class AllNotebooksPage(GenericPage):
    def get(self):
        self.render("under_construction.html")
