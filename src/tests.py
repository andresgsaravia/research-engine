# Some tests

from generic import *

class BigPage(GenericPage):
    def get(self):
        self.render("test_big_page.html")
