# Your knowledge database

from generic import *

## Handlers ##

class MainPage(GenericPage):
    def get(self):
        self.write("library's main page.")

class Articles(GenericPage):
    def get(self):
        self.write("Your articles in the knowledge database.")

class BlogPosts(GenericPage):
    def get(self):
        self.write("Your blog posts in the knowledge database.")

class Software(GenericPage):
    def get(self):
        self.write("Your software in the knowledge database.")

class New(GenericPage):
    def get(self):
        self.render("new_knowledge.html")
