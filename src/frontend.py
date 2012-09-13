# main.py

from generic import *

class MainPage(GenericPage):
    def get(self):
        self.render("base.html")
