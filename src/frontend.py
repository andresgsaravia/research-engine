# frontend.py

from generic import *

class RootPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        projects = user.list_of_projects() if user else []
        recent_actv = user.get_recent_activity() if user else []
        self.render("root.html", user = user, projects = projects, recent_actv = recent_actv)

    def post(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/")
            return
        action = self.request.get("action")
        recent_actv = user.get_recent_activity()
        if action == "MarkProjectActvAsRead":
            for p_key in recent_actv["Projects"]:
                for a in recent_actv["Projects"][p_key][1]:
                    a.seen_p = True
                    self.log_and_put(a)
        self.redirect("/")

class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")

class RemoveTrailingSlash(webapp2.RequestHandler):
    def get(self, url):
        self.redirect("/" + url)
