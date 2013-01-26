# wiki.py
# A wiki for each project.

from generic import *
import projects


###########################
##   Datastore Objects   ##
###########################

# Each WikiPage should have a project as parent.
class WikiPages(db.Model):
    url = db.StringProperty(required = True)
    content = db.TextProperty(required = True)      # Should be equal to the lastest WikiRevision's content


# Each WikiRevision should have a WikiPage as parent.
class WikiRevisions(db.Model):
    author = db.ReferenceProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    content = db.TextProperty(required = True)
    summary = db.StringProperty(required = False)


######################
##   Web Handlers   ##
######################

class ViewWikiPage(GenericPage):
    def get(self, username, projectname, wikiurl):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        wikipage = WikiPages.all().ancestor(project).filter("url =", wikiurl.lower()).get()
        self.render("wiki_view.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage)


class EditWikiPage(GenericPage):
    def get(self, username, projectname, wikiurl):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        self.render("wiki_edit.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage)

    def post(self, username, projectname, wikiurl):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        content = self.request.get("content")
        summary = self.request.get("summary")
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author in this project. "
        if not content:
            have_error = True
            error_message = "You must write some content before saving. "
        if wikipage and (wikipage.content == content):
            have_error = True
            error_message = "There aren't any changes to save. "
        if not have_error:
            if not wikipage:
                wikipage = WikiPages(url = wikiurl.lower(), content = content, parent = project)
                self.log_and_put(wikipage, "New instance. ")
            else:
                wikipage.content = content
                self.log_and_put(wikipage, "Changing content." )
            new_revision = WikiRevisions(author = user.key(), content = content, summary = summary,
                                         parent = wikipage)
            self.log_and_put(new_revision)
            self.redirect("/%s/%s/wiki/page/%s" % (username, projectname, wikiurl))
        else:
            self.render("wiki_edit.html", p_author = p_author, project = project, wikipage = wikipage,
                        wikiurl = wikiurl, wikitext = content, error_message = error_message)


class HistoryWikiPage(GenericPage):
    def get(self, username, projectname, wikiurl):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        revisions = []
        if wikipage:
            for rev in WikiRevisions.all().ancestor(wikipage).order("-date").run():
                revisions.append(rev)
        self.render("wiki_history.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage, revisions = revisions)


class RevisionWikiPage(GenericPage):
    def get(self, username, projectname, wikiurl, rev_id):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        if not wikipage:
            self.error(404)
            self.render("404.html")
            return
        revision = WikiRevisions.get_by_id(int(rev_id), parent = wikipage)
        if not revision:
            self.error(404)
            self.render("404.html")
            return
        self.render("wiki_revision.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, revision = revision)
