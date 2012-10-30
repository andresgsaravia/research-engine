# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/new_user', users.NewUserPage),
                               ('/settings', users.SettingsPage),
                               # Library
                               ('/library', library.MainPage),
                               ('/library/new', library.New),
                               ('/library/item/edit/(.+)', library.Edit),
                               ('/library/item/(.+)', library.Item),
                               # Projects
                               ('/projects', projects.MainPage),
                               ('/projects/new', projects.NewProjectPage),
                               ('/projects/project/edit/(.+)', projects.EditProjectPage),
                               ('/projects/project/new_resource/(.+)', projects.NewResourcePage),
                               ('/projects/project/(.+)', projects.ProjectPage),
                               # Notebooks
                               ('/notebooks', notebooks.MainPage),
                               ('/notebooks/new', notebooks.NewNotebookPage),
                               ('/notebooks/notebook/edit/(.+)', notebooks.EditNotebookPage),
                               ('/notebooks/notebook/new_entry/(.+)', notebooks.NewEntryPage),
                               ('/notebooks/notebook/(.+)', notebooks.NotebookPage),
                               # Empty placeholders
                               ('/news', frontend.UnderConstructionPage),
                               ('/notebooks', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               ('/collaborations', frontend.UnderConstructionPage),
                               # Tests
                               ("/tests/big_page", tests.BigPage)],
                              debug = True)
