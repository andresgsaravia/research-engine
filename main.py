# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/settings', users.SettingsPage),
                               ('/user/search', users.SearchForUserPage),
                               ('/user/contacts', users.ContactsPage),
                               ('/user/(.+)', users.UserPage),
                               # Projects
                               ('/projects', projects.MainPage),
                               ('/projects/new', projects.NewProjectPage),
                               ('/projects/recent_activity', projects.RecentActivityPage),
                               ('/projects/project/edit/(.+)', projects.EditProjectPage),
                               ('/projects/project/new_reference/(.+)', projects.NewReferencePage),
                               ('/projects/project/new_notebook/(.+)', projects.NewNotebookPage),
                               ('/projects/project/(.+)/nb/edit/(.+)', projects.EditNotebookPage),
                               ('/projects/project/(.+)/nb/note/(.+)', projects.NotePage),
                               ('/projects/project/(.+)/nb/new_note/(.+)', projects.NewNotePage),
                               ('/projects/project/(.+)/nb/(.+)', projects.NotebookPage),
                               ('/projects/project/(.+)/ref/edit/(.+)', projects.EditReferencePage),
                               ('/projects/project/(.+)/ref/(.+)', projects.ReferencePage),
                               ('/projects/project/(.+)', projects.ProjectPage),
                               # Empty placeholders
                               ('/news', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               ('/collaborations', frontend.UnderConstructionPage),
                               # Tests
                               ("/tests/big_page", tests.BigPage)],
                              debug = True)
