# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users module
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/new_user', users.NewUserPage),
                               ('/settings', users.SettingsPage),
                               # Library module
                               ('/library', library.MainPage),
                               ('/library/new', library.New),
                               ('/library/item/edit/(.+)', library.Edit),
                               ('/library/item/(.+)', library.Item),
                               # Projects module
                               ('/projects', projects.MainPage),
                               ('/projects/new', projects.NewProjectPage),
                               ('/projects/project/edit/(.+)', projects.EditProjectPage),
                               ('/projects/project/new_resource/(.+)', projects.NewResourcePage),
                               ('/projects/project/(.+)', projects.ProjectPage),
                               # Empty placeholders
                               ('/news', frontend.UnderConstructionPage),
                               ('/notebooks', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               ('/collaborations', frontend.UnderConstructionPage),
                               # Tests
                               ("/tests/big_page", tests.BigPage)],
                              debug = True)
