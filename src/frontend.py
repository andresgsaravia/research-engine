# frontend.py

from generic import *

class RootPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        projects = user.list_of_projects() if user else []
        recent_actv = user.get_recent_activity() if user else []
        self.render("root.html", user = user, projects = projects, recent_actv = recent_actv)

class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")

class RemoveTrailingSlash(webapp2.RequestHandler):
    def get(self, url):
        self.redirect("/" + url)
