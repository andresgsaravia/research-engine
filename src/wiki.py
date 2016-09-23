# wiki.py
# A wiki for each project.

from google.appengine.ext import ndb
import re
import generic, projects, groups

###########################
##   Datastore Objects   ##
###########################

# Each WikiPage should have a Project as parent.
class WikiPages(ndb.Model):
    url = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)      # Should be equal to the lastest WikiRevision's content

    def is_open_p(self):
        return self.key.parent().get().wiki_open_p

# Each WikiRevision should have a WikiPage as parent.
class WikiRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    content = ndb.TextProperty(required = True)
    summary = ndb.StringProperty(required = False)

    def is_open_p(self):
        return self.key.parent().get().is_open_p()


# Each comment should be a parent of a WikiPage
class WikiComments(ndb.Model):
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def is_open_p(self):
        return self.key.parent().get().is_open_p()


######################
##   Web Handlers   ##
######################

class GenericWikiPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, wiki_tab_class = "active", *a, **kw)

    def get_wikipage(self, project, url, log_message = ''):
        url = url.strip().replace(" ", "_")
        self.log_read(WikiPages, log_message)
        return WikiPages.query(WikiPages.url == url, ancestor = project.key).get()

    def get_revisions(self, wikipage, log_message = ''):
        revisions = []
        if not wikipage: return []
        for rev in WikiRevisions.query(ancestor = wikipage.key).order(-WikiRevisions.date).iter():
            self.log_read(WikiRevisions, log_message)
            revisions.append(rev)
        return revisions

    def get_revision(self, wikipage, revid, log_message = ''):
        self.log_read(WikiRevisions, log_message)
        return WikiRevisions.get_by_id(int(revid), parent = wikipage.key)

    def get_comments_list(self, wikipage):
        self.log_read(WikiComments, "Fetching all the comments in the Talk page for a wiki page. ")
        return WikiComments.query(ancestor = wikipage.key).order(-WikiComments.date).fetch()


class RedirectMainPage(GenericWikiPage):
    def get(self, projectid):
        self.redirect("/%s/wiki/page/Main_Page" % projectid)


class ViewWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not (project.wiki_open_p or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        wikitext = wikipage.content if wikipage else ''
        self.render("wiki_view.html", project = project, view_p = True, 
                    visitor_p = not (user and project.user_is_author(user)),
                    wikiurl = wikiurl, wikipage = wikipage, wikitext = wikitext)

    def post(self, projectid, wikiurl):
        # Toggle visibility code here... tomorrow
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/wiki/page/%s" % (projectid, wikiurl))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        action = self.request.get("action")
        if not (project.user_is_author(user) 
                and action == "toggle_visibility" 
                and wikiurl == "Main_Page"):
            self.redirect("/%s/wiki/page/%s" % (projectid, wikiurl))
            return
        project.wiki_open_p = not project.wiki_open_p 
        self.log_and_put(project)
        self.redirect("/%s/wiki/page/Main_Page" % projectid)


class EditWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/wiki/edit/%s" % (projectid, wikiurl))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/wiki/page/%s" % (projectid, wikiurl))
            return
        wikipage = self.get_wikipage(project, wikiurl)
        self.render("wiki_edit.html", project = project,
                    wikiurl = wikiurl, wikipage = wikipage, edit_p = True)

    def post(self, projectid, wikiurl):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/wiki/edit/%s" % (projectid, wikiurl))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/wiki/page/%s" % (projectid, wikiurl))
            return
        content = self.request.get("content")
        summary = self.request.get("summary")
        wikipage = self.get_wikipage(project, wikiurl)
        have_error = False
        error_message = ''
        if not content:
            have_error = True
            error_message = "You must write some content before saving. "
        if wikipage and (wikipage.content == content):
            have_error = True
            error_message = "There aren't any changes to save. "
        if not have_error:
            if not wikipage:
                wikipage = WikiPages(url = wikiurl, content = content, parent = project.key)
                self.log_and_put(wikipage, "New instance. ")
            else:
                wikipage.content = content
                self.log_and_put(wikipage, "Changing content." )
            new_revision = WikiRevisions(author = user.key, content = content, summary = summary,
                                         parent = wikipage.key)
            self.put_and_report(new_revision, user, project)
            self.redirect("/%s/wiki/page/%s" % (projectid, wikiurl))
        else:
            self.render("wiki_edit.html", project = project, wikipage = wikipage, wikiurl = wikiurl,
                        wikitext = content, error_message = error_message, editClass = "active")


class HistoryWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not (project.wiki_open_p or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        revisions = self.get_revisions(wikipage)
        self.render("wiki_history.html", project = project, hist_p = True,
                    visitor_p = not (user and project.user_is_author(user)),
                    wikiurl = wikiurl, wikipage = wikipage, revisions = revisions)


class RevisionWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl, revid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not (project.wiki_open_p or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        if not wikipage:
            self.error(404)
            self.render("404.html", info = 'Page "%s" not found in this wiki.' % wikipage.url.replace("_"," ").title())
            return
        revision = self.get_revision(wikipage, revid)
        if not revision:
            self.error(404)
            self.render("404.html", info = "Revision %s not found" % revid)
            return
        wikitext = revision.content if revision else ''
        self.render("wiki_revision.html", project = project, hist_p = True,
                    visitor_p = not (user and project.user_is_author(user)),
                    wikiurl = wikiurl, revision = revision, wikitext = wikitext)

class TalkWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not (project.wiki_open_p or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return        
        wikipage = self.get_wikipage(project, wikiurl)
        if not wikipage:
            self.error(404)
            self.render("wiki_view.html", wikipage = False, project = project, wikiurl = wikiurl, talk_p = True)
            return
        comments = self.get_comments_list(wikipage)
        self.render("wiki_talk.html", project = project, error_message = self.request.get("error"),
                    wikiurl = wikiurl, comments = comments, talk_p = True)

    def post(self, projectid, wikiurl):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, noteid))
            return
        wikipage = self.get_wikipage(project, wikiurl)
        if not wikipage:
            self.error(404)
            self.render("404.html", info = 'Page "%s" not found in this wiki.' % wikipage.url.replace("_"," ").title())
            return
        have_error = False
        error_message = ""
        comment = self.request.get("comment")
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            comment_id = self.request.get("comment_id")   # If this is present, we are editing a comment, otherwise it's a new comment
            if comment_id:
                # Edit comment
                c = WikiComments.get_by_id(int(comment_id), parent = wikipage.key)
                c.comment = comment
                self.log_and_put(c)
            else:
                # New comment
                new_comment = WikiComments(author = user.key, comment = comment, parent = wikipage.key)
                self.put_and_report(new_comment, user, project, wikipage)
#        if not have_error:
#            new_comment = WikiComments(author = user.key, comment = comment, parent = wikipage.key)
 #           self.put_and_report(new_comment, user, project, wikipage)
        self.redirect("/%s/wiki/talk/%s" % (projectid, wikiurl) + "?error=%s" % error_message if error_message else '')

