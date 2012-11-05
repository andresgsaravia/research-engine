# notebooks.py
# Creating and managing notebooks.

from generic import *

SHORT_DESCRIPTION_LENGTH = 150

##########################
##   Helper Functions   ##
##########################


###########################
##   Datastore Objects   ##
###########################

# Each Notebook is parent to its NotebookNotes.
class Notebooks(db.Model):
    owner = db.ReferenceProperty(required = True)
    name = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    started = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)

    def full_render(self):
        params = {}
        params["notebook"] = self
        params["n_description"] = self.description.replace("\n", "<br/>")
        params["last_note"] = self.last_updated.strftime("%d-%b-%Y")
        params["started"] = self.started.strftime("%d-%b-%Y")
        return render_str("notebook_full.html", **params)

    def short_render(self):
        last_note_date = self.last_updated.strftime("%d-%b-%Y")
        return render_str("notebook_short.html", notebook = self, last_note_date = last_note_date)

    def short_description(self):
        if len(self.description) < SHORT_DESCRIPTION_LENGTH:
            return self.description
        else:
            return self.description[0:SHORT_DESCRIPTION_LENGTH - 3] + "..."

# Each NotebookNote should have as parent one Notebook. Comments to notes are children.
# Adding a new comment should cause and update in the parent Notebook's last_updated property.
class NotebookNotes(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    added = db.DateTimeProperty(auto_now_add = True)


# Each NoteComment should have as parent one NotebookNote.
class NoteComments(db.Model):
    content = db.TextProperty(required = True)
    author = db.ReferenceProperty(required = True)
    added = db.DateTimeProperty(auto_now_add = True)


######################
##   Web Handlers   ##
######################

class MainPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebooks = []
        for notebook_key in user.my_notebooks:
            notebook = self.get_item_from_key(notebook_key)
            if notebook: notebooks.append(notebook)
        notebooks.sort(key=lambda n: n.last_updated, reverse = True)
        self.render("notebooks_main.html", user = user, notebooks = notebooks)


class NewNotebookPage(GenericPage):
    def get(self):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        self.render("notebooks_new.html")

    def post(self):
        user = self.get_user()
        if not user:
            self.redirec("/login")
            return
        n_name = self.request.get("n_name")
        n_description = self.request.get("n_description")
        have_error = False
        error = ''
        if not n_name:
            have_error = True
            error += "Please provide a name for your new notebook. "
        if not n_description:
            have_error = True
            error += "Please provide a brief decription of your new notebook. "
        if have_error:
            self.render("notebooks_new.html", n_name = n_name, n_description = n_description, error = error)
        else:
            logging.debug("DB READ: Checking if user has a notebook with a given name to make a new one if not.")
            nb = Notebooks.all().filter("owner =", user).filter("name =", n_name).get()
            if nb:
                error += "You already have a notebook with that name, please choose another name."
                self.render("notebooks_new.html", n_name = n_name, n_description = n_description, error = error)
            else:
                new_notebook = Notebooks(owner = user.key(), name = n_name, description = n_description)
                logging.debug("DB WRITE: Creating a new notebook.")
                new_notebook.put()
                user.my_notebooks.append(new_notebook.key())
                logging.debug("DB WRITE: Appending a notebook to a user's my_notebooks list.")
                user.put()
                self.redirect("/notebooks/notebook/%s" % new_notebook.key())



class EditNotebookPage(GenericPage):
    def get(self, notebook_key):
        self.render("under_construction.html")


class NewNotePage(GenericPage):
    def get(self, notebook_key):
        self.render("under_construction.html")


# Needs to handle the case in which notebook_key is invalid
class NotebookPage(GenericPage):
    def get(self, notebook_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        notebook = self.get_item_from_key(db.Key(notebook_key))
        self.render("notebook.html", notebook = notebook, notes = [])
