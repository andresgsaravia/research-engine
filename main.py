# Main file
# Basically it just loads everything

import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.RootPage),
                               ('/(.+)/', frontend.RemoveTrailingSlash),
                               # Users
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/settings', users.SettingsPage),
                               ('/recover_password', users.RecoverPasswordPage),                       # Needs review
                               ('/verify_email', users.VerifyEmailPage),
                               ('/recover_password', users.RecoverPasswordPage),
                               # Cron jobs
                               ('/cron/send_email_notifications', email_messages.SendNotifications),
                               
                               ('/new_project', projects.NewProjectPage),
                               # Notebooks
                               ('/([0-9]+)/notebooks', notebooks.NotebooksListPage),                  # Argument is projects' integer id
                               ('/([0-9]+)/notebooks/new', notebooks.NewNotebookPage),
                               ('/([0-9]+)/notebooks/(.+)/([0-9]+)/edit', notebooks.EditNotePage),    # Last argument is the note's integer id
                               ('/([0-9]+)/notebooks/(.+)/([0-9]+)', notebooks.NotePage),    
                               ('/([0-9]+)/notebooks/(.+)/new_note', notebooks.NewNotePage),          # Last argument is the notebook's integer id
                               ('/([0-9]+)/notebooks/(.+)/edit', notebooks.EditNotebookPage), 
                               ('/([0-9]+)/notebooks/(.+)', notebooks.NotebookMainPage),
                               # Collaborative writings
                               ('/([0-9]+)/writings', collab_writing.WritingsListPage),
                               ('/([0-9]+)/writings/new', collab_writing.NewWritingPage),
                               ('/([0-9]+)/writings/([0-9]+)/edit', collab_writing.EditWritingPage),
                               ('/([0-9]+)/writings/([0-9]+)/discussion', collab_writing.DiscussionPage),
                               ('/([0-9]+)/writings/([0-9]+)/history', collab_writing.HistoryWritingPage),
                               ('/([0-9]+)/writings/([0-9]+)/info', collab_writing.InfoPage),
                               ('/([0-9]+)/writings/([0-9]+)/rev/([0-9]+)', collab_writing.ViewRevisionPage),
                               ('/([0-9]+)/writings/([0-9]+)', collab_writing.ViewWritingPage),
                               # Forum
                               ('/([0-9]+)/forum', forum.MainPage),
                               ('/([0-9]+)/forum/new_thread', forum.NewThreadPage),
                               ('/([0-9]+)/forum/([0-9]+)/edit', forum.EditThreadPage),
                               ('/([0-9]+)/forum/([0-9]+)', forum.ThreadPage),
                               # Wiki
                               ('/([0-9]+)/wiki/page/(.+)', wiki.ViewWikiPage),
                               ('/([0-9]+)/wiki/edit/(.+)', wiki.EditWikiPage),
                               ('/([0-9]+)/wiki/history/(.+)/rev/([0-9]+)', wiki.RevisionWikiPage),
                               ('/([0-9]+)/wiki/history/(.+)', wiki.HistoryWikiPage),
                               # Datasets
                               ('/([0-9]+)/datasets', datasets.MainPage),
                               ('/([0-9]+)/datasets/new', datasets.NewDataSetPage),
                               ('/([0-9]+)/datasets/([0-9]+)', datasets.DataSetPage),
                               ('/([0-9]+)/datasets/([0-9]+)/edit', datasets.EditDataSetPage),
                               ('/([0-9]+)/datasets/([0-9]+)/new_data', datasets.NewDataConceptPage),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)', datasets.DataConceptPage),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)/new', datasets.NewDataRevisionPage),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)/edit', datasets.EditConceptPage),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)/upload', datasets.UploadDataRevisionHandler),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)/edit/([0-9]+)', datasets.EditRevisionPage),
                               ('/([0-9]+)/datasets/([0-9]+)/([0-9]+)/update/([0-9]+)', datasets.UpdateDataRevisionHandler),
                               # Code
                               ('/([0-9]+)/code', code.CodesListPage),
                               ('/([0-9]+)/code/new', code.NewCodePage),
                               ('/([0-9]+)/code/([0-9]+)', code.ViewCodePage),
                               # Bibliography
                               ('/([0-9]+)/bibliography', bibliography.MainPage),
                               ('/([0-9]+)/bibliography/new_item', bibliography.NewItemPage),
                               ('/([0-9]+)/bibliography/([0-9]+)/([0-9]+)', bibliography.CommentPage),
                               ('/([0-9]+)/bibliography/([0-9]+)', bibliography.ItemPage),
                               # Admin projects
                               ('/([0-9]+)/admin', projects.AdminPage),
                               ('/([0-9]+)/invite', projects.InvitePage),
                               ('/file/(.+)', datasets.DownloadDataRevisionHandler),                                    # Argument is the Blobstore key

                               ('/([0-9]+)', projects.OverviewPage),
                               ('/(.+)', users.UserPage)],
                              debug = True)

