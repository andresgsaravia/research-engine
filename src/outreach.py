# outreach.py
# All related to public outreach

from google.appengine.ext import ndb
import generic, projects

###########################
##   Datastore Objects   ##
###########################


######################
##   Web Handlers   ##
######################

class MainPage(generic.GenericPage):
    def get(self, username):
        user = self.get_login_user()
        page_user = self.get_user_by_username(username)
        if not page_user:
            self.render("404.html", info = "User %s not found." % username)
            return
        self.render("outreach_MainPage.html", page_user = page_user, user = user)
    
