# main.py

from generic import *

class MainPage(GenericPage):
    def get(self):
        self.render("base.html")

class UnderConstructionPage(GenericPage):
    def get(self):
        self.render("under_construction.html")
