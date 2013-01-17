# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users
                               ('/login', users.LoginPage),           # Needs review
                               ('/logout', users.LogoutPage),           # Needs review
                               ('/signup', users.SignupPage),           # Needs review
                               ('/settings', users.SettingsPage),           # Needs review
                               ('/user/search', users.SearchForUserPage),           # Needs review
                               ('/contacts', users.ContactsPage),           # Needs review
                               ('/recover_password', users.RecoverPasswordPage),           # Needs review
                               ('/verify_email', users.VerifyEmailPage),           # Needs review

                               ('/(.+)/new_project', projects.NewProjectPage),          # Argument is username
                               ('/(.+)/(.+)/notebooks', notebooks.NotebooksListPage),   # Arguments are username and project_name
                               ('/(.+)/(.+)/notebooks/new', notebooks.NewNotebookPage),
                               ('/(.+)/(.+)', projects.OverviewPage),                   
                               # ('/projects/recent_activity', projects.RecentActivityPage),           # Needs review
                               # ('/projects/project/edit/(.+)', projects.EditProjectPage),           # Needs review
                               # ('/projects/project/new_reference/(.+)', references.NewReferencePage),           # Needs review
                               # ('/projects/project/new_notebook/(.+)', notebooks.NewNotebookPage),           # Needs review
                               # ('/projects/project/new_writing/(.+)', collab_writing.NewWritingPage),           # Needs review
                               # ('/projects/project/(.+)/nb/edit/(.+)', notebooks.EditNotebookPage),           # Needs review
                               # ('/projects/project/(.+)/nb/note/(.+)', notebooks.NotePage),           # Needs review
                               # ('/projects/project/(.+)/nb/new_note/(.+)', notebooks.NewNotePage),           # Needs review
                               # ('/projects/project/(.+)/nb/edit_note/(.+)', notebooks.EditNotePage),           # Needs review
                               # ('/projects/project/(.+)/nb/(.+)', notebooks.NotebookPage),           # Needs review
                               # ('/projects/project/(.+)/ref/edit/(.+)', references.EditReferencePage),           # Needs review
                               # ('/projects/project/(.+)/ref/(.+)', references.ReferencePage),           # Needs review
                               # ('/projects/project/(.+)/cwriting/view/(.+)', collab_writing.ViewRevisionPage),           # Needs review
                               # ('/projects/project/(.+)/cwriting/edit/(.+)', collab_writing.EditWritingPage),           # Needs review
                               # ('/projects/project/(.+)/cwriting/(.+)', collab_writing.WritingPage),           # Needs review
                               # ('/notebooks', notebooks.AllNotebooksPage),           # Needs review
                               # ('/news', frontend.UnderConstructionPage),           # Needs review
                               # ('/classroom', frontend.UnderConstructionPage),           # Needs review                               

                               ('/(.+)', users.UserPage)],           # Needs review
                              debug = True)


# I want this structure:
 
# TODO     /                                     Main site page
# TODO     /login
# TODO     /logout
# TODO     /signup
# TODO     /recover_password
# TODO     /verify_email
# TODO     /settings                             Edit user's settings
 
# TODO     /(username)                           View profile and list projects
# TODO     /(username)/contacts                  List of contacts
# TODO     /(username)/new_project
# ----     /(username)/(project_name)            News and overview
# TODO     /(username)/(project_name)/wiki
# TODO     /(username)/(project_name)/forum
# ----     /(username)/(project_name)/notebooks
# ----     /(username)/(project_name)/notebooks/new
# TODO     /(username)/(project_name)/notebooks/(notebook_name)
# TODO     /(username)/(project_name)/writings
# TODO     /(username)/(project_name)/writings/new
# TODO     /(username)/(project_name)/writings/(writing_id)
# TODO     /(username)/(project_name)/references
# TODO     /(username)/(project_name)/references/new
# TODO     /(username)/(project_name)/references/(reference_id)
# TODO     /(username)/(project_name)/code
# TODO     /(username)/(project_name)/datasets
# TODO     /(username)/(project_name)/admin   # Perhaps from here I should add a collaborator.
# TODO     /(username)/classroom       I still need to figure out this part
