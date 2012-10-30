# notebooks.py
# Creating and managing notebooks.

from generic import *


##########################
##   Helper Functions   ##
##########################


###########################
##   Datastore Objects   ##
###########################


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

