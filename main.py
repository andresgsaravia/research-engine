# Main file
# Basically it just loads everything

import os, sys
lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

from webapp2 import WSGIApplication, Route
from src.secrets import SESSION_KEY

app_config = {
  'webapp2_extras.sessions': {
    'cookie_name': '_simpleauth_sess',
    'secret_key': SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_attributes': []
  }
}

routes = [
    Route('/', handler='src.frontend.RootPage'),
    Route('/<:.+>/', 'src.frontend.RemoveTrailingSlash'),
    Route('/terms', 'src.frontend.TermsOfServicePage'),
    Route('/_preview', 'src.generic.RenderPreview'),
    # Users
    Route('/login', 'src.users.LoginPage'),
    Route('/signup', 'src.users.SignupPage'),
    Route('/settings', 'src.users.SettingsPage'),
    Route('/recover_password', 'src.users.RecoverPasswordPage'),
    Route('/verify_email', 'src.users.VerifyEmailPage'),
    Route('/auth/<provider>', handler='src.users.AuthHandler:_simple_auth', name='auth_login'),
    Route('/auth/<provider>/callback', handler='src.users.AuthHandler:_auth_callback', name='auth_callback'),
    Route('/logout', handler='src.users.AuthHandler:logout', name='logout'),
    # Cron jobs
    Route('/cron/send_email_notifications', 'src.email_messages.SendNotifications'),
    Route('/cron/send_group_biblio_notifications', 'src.groups.SendBiblioNotifications'),
    Route('/cron/send_pending_emails', 'src.email_messages.SendPendingEmails'),
    ##
    #  Projects
    ##
    Route('/new_project', 'src.projects.NewProjectPage'),
    # Notebooks
    Route('/<projectid:[0-9]+>/notebooks', 'src.notebooks.NotebooksListPage'),
    Route('/<projectid:[0-9]+>/notebooks/new', 'src.notebooks.NewNotebookPage'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/<noteid:[0-9]+>/edit', 'src.notebooks.EditNotePage'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/<noteid:[0-9]+>', 'src.notebooks.NotePage'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/new_note', 'src.notebooks.NewNotePage'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/edit', 'src.notebooks.EditNotebookPage'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/_utils/index', handler='src.notebooks.NotebookUtils:index'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>/_utils/html_export', handler='src.notebooks.NotebookUtils:html_export'),
    Route('/<projectid:[0-9]+>/notebooks/<nbid:[0-9]+>', 'src.notebooks.NotebookMainPage'),
    # Collaborative writings
    Route('/<projectid:[0-9]+>/writings', 'src.collab_writing.WritingsListPage'),
    Route('/<projectid:[0-9]+>/writings/new', 'src.collab_writing.NewWritingPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/edit', 'src.collab_writing.EditWritingPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/discussion', 'src.collab_writing.DiscussionPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/history', 'src.collab_writing.HistoryWritingPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/info', 'src.collab_writing.InfoPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/rev/<revid:[0-9]+>', 'src.collab_writing.ViewRevisionPage'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>/_html', handler='src.collab_writing.WritingUtils:html_export'),
    Route('/<projectid:[0-9]+>/writings/<writingid:[0-9]+>', 'src.collab_writing.ViewWritingPage'),
    # Forum
    Route('/<projectid:[0-9]+>/forum', 'src.forum.MainPage'),
    Route('/<projectid:[0-9]+>/forum/new_thread', 'src.forum.NewThreadPage'),
    Route('/<projectid:[0-9]+>/forum/<threadid:[0-9]+>/edit', 'src.forum.EditThreadPage'),
    Route('/<projectid:[0-9]+>/forum/<threadid:[0-9]+>', 'src.forum.ThreadPage'),
    # Wiki
    Route('/<projectid:[0-9]+>/wiki/page/<wikiurl:.+>', 'src.wiki.ViewWikiPage'),
    Route('/<projectid:[0-9]+>/wiki/edit/<wikiurl:.+>', 'src.wiki.EditWikiPage'),
    Route('/<projectid:[0-9]+>/wiki/history/<wikiurl:.+>/rev/<revid:[0-9]+>', 'src.wiki.RevisionWikiPage'),
    Route('/<projectid:[0-9]+>/wiki/history/<wikiurl:.+>', 'src.wiki.HistoryWikiPage'),
    Route('/<projectid:[0-9]+>/wiki/talk/<wikiurl:.+>', 'src.wiki.TalkWikiPage'),
    # Datasets
    Route('/<projectid:[0-9]+>/datasets', 'src.datasets.MainPage'),
    Route('/<projectid:[0-9]+>/datasets/new', 'src.datasets.NewDataSetPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>', 'src.datasets.DataSetPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/edit', 'src.datasets.EditDataSetPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/new_data', 'src.datasets.NewDataConceptPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>', 'src.datasets.DataConceptPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>/new', 'src.datasets.NewDataRevisionPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>/edit', 'src.datasets.EditConceptPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>/upload', 'src.datasets.UploadDataRevisionHandler'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>/edit/<revid:[0-9]+>', 'src.datasets.EditRevisionPage'),
    Route('/<projectid:[0-9]+>/datasets/<datasetid:[0-9]+>/<datacid:[0-9]+>/update/<revid:[0-9]+>', 'src.datasets.UpdateDataRevisionHandler'),
    # Images
    Route('/<projectid:[0-9]+>/images', 'src.images.MainPage'),
    Route('/<projectid:[0-9]+>/images/new', 'src.images.NewImagePage'),
    Route('/<projectid:[0-9]+>/images/new_image', 'src.images.UploadNewImage'),
    Route('/<projectid:[0-9]+>/images/<imageid:[0-9]+>/edit', 'src.images.EditImagePage'),
    Route('/<projectid:[0-9]+>/images/<imageid:[0-9]+>/edit_image', 'src.images.EditImage'),
    # Code
    Route('/<projectid:[0-9]+>/code', 'src.code.CodesListPage'),
    Route('/<projectid:[0-9]+>/code/new', 'src.code.NewCodePage'),
    Route('/<projectid:[0-9]+>/code/<codeid:[0-9]+>/edit', 'src.code.EditCodePage'),
    Route('/<projectid:[0-9]+>/code/<codeid:[0-9]+>', 'src.code.ViewCodePage'),
    # Bibliography
    Route('/<projectid:[0-9]+>/bibliography', 'src.bibliography.MainPage'),
    Route('/<projectid:[0-9]+>/bibliography/new_item', 'src.bibliography.NewItemPage'),
    Route('/<projectid:[0-9]+>/bibliography/<itemid:[0-9]+>/<commentid:[0-9]+>', 'src.bibliography.CommentPage'),
    Route('/<projectid:[0-9]+>/bibliography/<itemid:[0-9]+>', 'src.bibliography.ItemPage'),
    # Admin projects
    Route('/<projectid:[0-9]+>/admin', 'src.projects.AdminPage'),
    Route('/<projectid:[0-9]+>/invite', 'src.projects.InvitePage'),
    Route('/file/<blobkey:.+>', 'src.datasets.DownloadDataRevisionHandler'),
    
    Route('/<projectid:[0-9]+>', 'src.frontend.OverviewPage'),
    # Groups
    Route('/new_group', 'src.groups.NewGroupPage'),
    Route('/g/<groupid:[0-9]+>', 'src.groups.ViewGroupPage'),
    Route('/g/<groupid:[0-9]+>/calendar/new', 'src.groups.CalendarNewTask'),
    Route('/g/<groupid:[0-9]+>/calendar', 'src.groups.CalendarPage'),
    Route('/g/<groupid:[0-9]+>/_edit_event/<eventid:[0-9]+>', 'src.groups.EditEvent'),
    Route('/g/<groupid:[0-9]+>/admin', 'src.groups.AdminPage'),
    Route('/g/<groupid:[0-9]+>/invited', 'src.groups.InvitedPage'),
    Route('/g/<groupid:[0-9]+>/bibliography', 'src.groups.BiblioPage'),

    Route('/<username:.+>/outreach', 'src.outreach.MainPage'),
    Route('/<username:.+>/outreach/new_post', 'src.outreach.NewPostPage'),
    Route('/<username:.+>/outreach/<postid:[0-9]+>/edit', 'src.outreach.EditPostPage'),
    Route('/<username:.+>/outreach/<postid:[0-9]+>', 'src.outreach.ViewPostPage'),
    Route('/<username:.+>', 'src.users.UserPage')]


app = WSGIApplication(routes, config = app_config, debug = True)

