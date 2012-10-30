# notebooks.py
# Creating and managing notebooks.

from generic import *


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


# Each NotebookNote should have as parent one Notebook. Comments to notes are children.
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
        self.render("under_construction.html")


class NewNotebookPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class EditNotebookPage(GenericPage):
    def get(self, notebook_key):
        self.render("under_construction.html")


class NewEntryPage(GenericPage):
    def get(self, notebook_key):
        self.render("under_construction.html")


class NotebookPage(GenericPage):
    def get(self, notebook_key):
        self.render("under_construction.html")

