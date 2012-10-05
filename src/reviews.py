# reviews.py
# Article and blog reviews

from generic import *

class MainPage(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("reviews.html")

class New(GenericPage):
    def get(self):
        self.render("new_entry.html")
