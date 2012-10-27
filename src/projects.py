# projects.py
# For creating, managing and updating projects.

from generic import *


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
    started = db.DateProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)
    
# Child of Projects
class ProjectEntries(db.Model):
    title = db.StringProperty(required = True)
    project_kind = db.StringProperty(required = True)
    date = db.DateProperty(auto_now_add = True)
    content = db.TextProperty(required = False)
    author = db.ReferenceProperty(required = True)


######################
##   Web Handlers   ##
######################

class MainPage(GenericPage):
    def get(self):
        user = self.get_user()
        self.render("projects_main.html")


class NewProjectPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class ProjectPage(GenericPage):
    def get(self, project_key):
        self.render("under_construction.html")
