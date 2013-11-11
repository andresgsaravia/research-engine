# frontend.py

from generic import *

class RootPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        projects = user.list_of_projects() if user else []
        p_updates = []
        if user:
            for p in projects:
                p_updates += p.list_updates(self)          # I query more items than needed... there should be a smart way to do this.
        p_updates.sort(key=lambda u: u.date, reverse = True)
        self.render("root.html", user = user, projects = projects, p_updates = p_updates[:30])


class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")


class RemoveTrailingSlash(webapp2.RequestHandler):
    def get(self, url):
        self.redirect("/" + url)


class TermsOfServicePage(GenericPage):
    def get(self):
        self.render("terms_of_service.html")
