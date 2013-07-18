# bibliography.py
# Bibliography review for a given project

from generic import *
import projects


###########################
##   Datastore Objects   ##
###########################

# Each BiblioItem should have a Project as parent
class BiblioItems(ndb.Model):
    title = ndb.StringProperty(required = True)
    link = ndb.StringProperty(required = True)
    kind = ndb.StringProperty(required = True)          # article, arXiv, book, etc...
    identifier = ndb.StringProperty(required = True)    # DOI, arXiv id, ISSN, etc...
    added = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

# Each BiblioComment should have a BiblioItem as parent
class BiblioComment(ndb.Model):
    content = ndb.TextProperty(required = True)
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)

######################
##   Web Handlers   ##
######################

class BiblioPage(projects.ProjectPage):
    pass


class MainPage(BiblioPage):
    def get(self, projectid):
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        self.render("biblio_main.html", project = project)
