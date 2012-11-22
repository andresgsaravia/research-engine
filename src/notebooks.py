# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *

SHORT_DESCRIPTION_LENGTH = 150

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

class NewNotebookPage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user: 
            self.redirect("/login")
            return
        self.render("notebook_new.html", project_key = project_key)

    def post(self, project_key):
        user = self.get_user()
        project = self.get_item_from_key_str(project_key)
        if not user:
            self.redirect("/login")
            return
        kw = {"n_name" : self.request.get("n_name"),
              "n_description" : self.request.get("n_description"),
              "error" : ''}
        have_error = False
        if not kw["n_name"]:
            have_error = True
            kw["error"] += 'You must provide a name for your new notebook. '
        if not kw["n_description"]:
            have_error = True
            kw["error"] += 'Please provide a brief description of your new notebook. '
        if not (user.key() in project.authors):
            have_error = True
            kw["error"] += "You can't add a notebook to this project since you are not one of its authors. "
        if have_error:
            self.render("notebook_new.html", **kw)
        else:
            new_notebook = Notebooks(owner = user.key(), name = kw["n_name"], description = kw["n_description"], 
                                     parent  = db.Key(project_key))
            self.log_and_put(new_notebook)
            user.my_notebooks.append(new_notebook.key())
            self.log_and_put(user, "Updating my_notebooks property. ")
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/projects/project/%s/nb/%s" % (project_key, new_notebook.key()))


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
