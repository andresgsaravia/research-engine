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
                               ('/projects', projects.ProjectsPage),
                               ('/projects/new', projects.NewProjectPage),
                               ('/projects/recent_activity', projects.RecentActivityPage),
                               ('/projects/project/edit/(.+)', projects.EditProjectPage),
                               ('/projects/project/new_reference/(.+)', references.NewReferencePage),
                               ('/projects/project/new_notebook/(.+)', notebooks.NewNotebookPage),
                               ('/projects/project/new_writing/(.+)', collab_writing.NewWritingPage),

                               ('/projects/project/(.+)/nb/edit/(.+)', notebooks.EditNotebookPage),
                               ('/projects/project/(.+)/nb/note/(.+)', notebooks.NotePage),
                               ('/projects/project/(.+)/nb/new_note/(.+)', notebooks.NewNotePage),
                               ('/projects/project/(.+)/nb/edit_note/(.+)', notebooks.EditNotePage),
                               ('/projects/project/(.+)/nb/(.+)', notebooks.NotebookPage),

                               ('/projects/project/(.+)/ref/edit/(.+)', references.EditReferencePage),
                               ('/projects/project/(.+)/ref/(.+)', references.ReferencePage),

                               ('/projects/project/(.+)/cwriting/view/(.+)', collab_writing.ViewRevisionPage),
                               ('/projects/project/(.+)/cwriting/edit/(.+)', collab_writing.EditWritingPage),
                               ('/projects/project/(.+)/cwriting/(.+)', collab_writing.WritingPage),

                               ('/projects/project/(.+)', projects.ProjectPage),
                               # Other
                               ('/notebooks', notebooks.AllNotebooksPage),
                               # Empty placeholders
                               ('/news', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               # Tests
                               ("/tests/big_page", tests.BigPage)],
                              debug = True)
