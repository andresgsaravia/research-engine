# frontend.py

from generic import *

class MainPage(GenericPage):
    def get(self):
        user = self.get_login_user()
        self.render("welcome.html", user = user)

class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")
