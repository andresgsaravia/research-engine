# Main file
# Basically it just loads everything

import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/settings', users.SettingsPage),                                      # Needs review
                               ('/user/search', users.SearchForUserPage),                              # Needs review
                               ('/recover_password', users.RecoverPasswordPage),                       # Needs review
                               ('/verify_email', users.VerifyEmailPage),
                               # Cron jobs
                               ('/cron/send_email_notifications', email_messages.SendNotifications),
                               
                               ('/(.+)/new_project', projects.NewProjectPage),                         # Argument is username
                               # Notebooks
                               ('/(.+)/(.+)/notebooks', notebooks.NotebooksListPage),                  # Arguments are username and projectname
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
                               ('/(.+)/(.+)/writings/([0-9]+)/discussion', collab_writing.DiscussionPage),
                               ('/(.+)/(.+)/writings/([0-9]+)/history', collab_writing.HistoryWritingPage),
                               ('/(.+)/(.+)/writings/([0-9]+)/info', collab_writing.InfoPage),
                               ('/(.+)/(.+)/writings/([0-9]+)/rev/([0-9]+)', collab_writing.ViewRevisionPage),
                               ('/(.+)/(.+)/writings/([0-9]+)', collab_writing.ViewWritingPage),
                               # Forum
                               ('/(.+)/(.+)/forum', forum.MainPage),
                               ('/(.+)/(.+)/forum/new_thread', forum.NewThreadPage),
                               ('/(.+)/(.+)/forum/([0-9]+)', forum.ThreadPage),
                               # Wiki
                               ('/(.+)/(.+)/wiki/page/(.+)', wiki.ViewWikiPage),
                               ('/(.+)/(.+)/wiki/edit/(.+)', wiki.EditWikiPage),
                               ('/(.+)/(.+)/wiki/history/(.+)/rev/([0-9]+)', wiki.RevisionWikiPage),
                               ('/(.+)/(.+)/wiki/history/(.+)', wiki.HistoryWikiPage),
                               # Datasets
                               ('/(.+)/(.+)/datasets', datasets.MainPage),
                               ('/(.+)/(.+)/datasets/new', datasets.NewDataSetPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)', datasets.DataSetPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/new_data', datasets.NewDataConceptPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)', datasets.DataConceptPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)/new', datasets.NewDataRevisionPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)/edit', datasets.EditConceptPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)/upload', datasets.UploadDataRevisionHandler),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)/edit/([0-9]+)', datasets.EditRevisionPage),
                               ('/(.+)/(.+)/datasets/([0-9]+)/([0-9]+)/update/([0-9]+)', datasets.UpdateDataRevisionHandler),
                               # Admin projects
                               ('/(.+)/(.+)/admin', projects.AdminPage),
                               ('/(.+)/(.+)/invite', projects.InvitePage),
                               ('/file/(.+)', datasets.DownloadDataRevisionHandler),                                    # Argument is the Blobstore key

                               ('/(.+)/(.+)', projects.OverviewPage),
                               ('/(.+)', users.UserPage)],
                              debug = True)

