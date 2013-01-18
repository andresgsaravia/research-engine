# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users
                               ('/login', users.LoginPage),                                            # Needs review
                               ('/logout', users.LogoutPage),                                          # Needs review
                               ('/signup', users.SignupPage),                                          # Needs review
                               ('/settings', users.SettingsPage),                                      # Needs review
                               ('/user/search', users.SearchForUserPage),                              # Needs review
                               ('/contacts', users.ContactsPage),                                      # Needs review
                               ('/recover_password', users.RecoverPasswordPage),                       # Needs review
                               ('/verify_email', users.VerifyEmailPage),                               # Needs review

                               ('/(.+)/new_project', projects.NewProjectPage),                         # Argument is username
                               # Notebooks
                               ('/(.+)/(.+)/notebooks', notebooks.NotebooksListPage),                  # Arguments are username and project_name
                               ('/(.+)/(.+)/notebooks/new', notebooks.NewNotebookPage),
                               ('/(.+)/(.+)/notebooks/(.+)/([0-9]+)/edit', notebooks.EditNotePage),    # Last argument is the note's numeric id
                               ('/(.+)/(.+)/notebooks/(.+)/([0-9]+)', notebooks.NotePage),    
                               ('/(.+)/(.+)/notebooks/(.+)/new_note', notebooks.NewNotePage),          # Last argument is the notebook name
                               ('/(.+)/(.+)/notebooks/(.+)/edit', notebooks.EditNotebookPage), 
                               ('/(.+)/(.+)/notebooks/(.+)', notebooks.NotebookMainPage),
                               # Collaborative writings
                               ('/(.+)/(.+)/writings', collab_writing.WritingsListPage),
                               ('/(.+)/(.+)/writings/new', collab_writing.NewWritingPage),
                               ('/(.+)/(.+)/writings/([0-9]+)/edit', collab_writing.EditWritingPage),
                               ('/(.+)/(.+)/writings/([0-9]+)/history', collab_writing.HistoryWritingPage),
#                               ('/(.+)/(.+)/writings/([0-9]+)/rev/([0-9]+)', collab_writing.ViewRevisionPage),
                               ('/(.+)/(.+)/writings/([0-9]+)', collab_writing.ViewWritingPage),
                               ('/(.+)/(.+)', projects.OverviewPage),                   
                               # ('/projects/recent_activity', projects.RecentActivityPage),           # Needs review
                               # ('/projects/project/edit/(.+)', projects.EditProjectPage),           # Needs review
                               # ('/projects/project/new_reference/(.+)', references.NewReferencePage),           # Needs review
                               # ('/projects/project/(.+)/ref/edit/(.+)', references.EditReferencePage),           # Needs review
                               # ('/projects/project/(.+)/ref/(.+)', references.ReferencePage),           # Needs review
                               # ('/news', frontend.UnderConstructionPage),           # Needs review
                               # ('/classroom', frontend.UnderConstructionPage),           # Needs review                               

                               ('/(.+)', users.UserPage)],                                             # Needs review
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
# TODO     /(username)/following                 
# TODO     /(username)/new_project
# ----     /(username)/(project_name)            News and overview
# TODO     /(username)/(project_name)/wiki
# TODO     /(username)/(project_name)/forum
# ----     /(username)/(project_name)/notebooks
# ----     /(username)/(project_name)/notebooks/new
# ----     /(username)/(project_name)/notebooks/(notebook_name)
# ----     /(username)/(project_name)/notebooks/(notebook_name)/new_note
# ----     /(username)/(project_name)/notebooks/(notebook_name)/edit
# ----     /(username)/(project_name)/notebooks/(notebook_name)/(note_id)
# ----     /(username)/(project_name)/notebooks/(notebook_name)/(note_id)/edit
# ----     /(username)/(project_name)/writings
# ----     /(username)/(project_name)/writings/new
# ----     /(username)/(project_name)/writings/(writing_id)
# ----     /(username)/(project_name)/writings/(writing_id)/edit
# ----     /(username)/(project_name)/writings/(writing_id)/history
# TODO     /(username)/(project_name)/writings/(writing_id)/rev/(revision_id)
# TODO     /(username)/(project_name)/writings/(writing_id)/discussion
# TODO     /(username)/(project_name)/writings/(writing_id)/info
# TODO     /(username)/(project_name)/references
# TODO     /(username)/(project_name)/references/new
# TODO     /(username)/(project_name)/references/(reference_id)
# TODO     /(username)/(project_name)/code
# TODO     /(username)/(project_name)/datasets
# TODO     /(username)/(project_name)/admin   # Perhaps from here I should add a collaborator.
# TODO     /(username)/classroom       I still need to figure out this part
