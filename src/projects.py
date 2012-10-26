# projects.py
# For creating, managing and updating projects.

from generic import *

######################
##   Web Handlers   ##
######################

class MainPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class NewProjectPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class ProjectPage(GenericPage):
    def get(self, project_key):
        self.render("under_construction.html")
