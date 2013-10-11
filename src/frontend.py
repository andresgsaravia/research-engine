# frontend.py

from generic import *

class RootPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        projects = user.list_of_projects() if user else []
        p_updates = []
        if user:
            for p in projects:
                p_updates.append((p, p.list_updates(self)))
        self.render("root.html", user = user, projects = projects, p_updates = p_updates)


class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class RemoveTrailingSlash(webapp2.RequestHandler):
    def get(self, url):
        self.redirect("/" + url)
