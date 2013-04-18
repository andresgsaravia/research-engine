# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
import projects

###########################
##   Datastore Objects   ##
###########################


######################
##   Web Handlers   ##
######################

class MainPage(projects.ProjectPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found' % project.name)
            return
        self.write(project.name + " will have a source code section here soon.")
