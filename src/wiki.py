# wiki.py
# A wiki for each project.

from generic import *
import projects

# This regexp finds MediaWiki-like inner links in the following way.
# A simple [[link and text]]                 -->   (''       , 'link and text')
# Another [[link | display text]]   -->   ('link |' , 'display text') 
WIKILINKS_RE = r'\[\[([^\|\]]+\|)?([^\]]+)\]\]'

# Given a link prefix and assuming the regex r'\[\[([^\|\]]+\|)?([^\]]+)\]\]'
# was used, this function returns the link and display text to be used un an
# html <a ...> tag.
def link_and_text(mobject, link_prefix):
    text = mobject.groups()[1].strip()
    if mobject.groups()[0]:
        link_posfix = mobject.groups()[0][:-1].strip().replace(" ","_")
    else:
        link_posfix = text.replace(" ", "_")
    link_posfix = link_posfix[:1].upper() + link_posfix[1:]
    return (link_prefix + link_posfix, text)

# Returns a function suitable to use inside a re.sub(...) call to generate
# a valid htlm <a ...> tag inside a wiki.
def make_sub_repl(projectid):
    link_prefix = "/%s/wiki/page/" % projectid
    return lambda x: '<a href="%s">%s</a>' % (link_and_text(x, link_prefix))


###########################
##   Datastore Objects   ##
###########################

# Each WikiPage should have a project as parent.
class WikiPages(ndb.Model):
    url = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)      # Should be equal to the lastest WikiRevision's content


# Each WikiRevision should have a WikiPage as parent.
class WikiRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    content = ndb.TextProperty(required = True)
    summary = ndb.StringProperty(required = False)

    def notification_html_and_txt(self, author, project, wikipage):
        kw = {"author" : author, "project" : project, "wikipage" : wikipage, "revision" : self,
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["wikipage_absolute_link"] = kw["project_absolute_link"] + "/wiki/page/" + wikipage.url
        return (render_str("emails/wiki.html", **kw), render_str("emails/wiki.txt", **kw))


######################
##   Web Handlers   ##
######################

class GenericWikiPage(projects.ProjectPage):
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

    def get_revision(self, wikipage, rev_id, log_message = ''):
        self.log_read(WikiRevisions, log_message)
        return WikiRevisions.get_by_id(int(rev_id), parent = wikipage.key)


class ViewWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        if wikipage: 
            wikitext = re.sub(WIKILINKS_RE, make_sub_repl(projectid), wikipage.content) 
        else:
            wikitext = '' 
        self.render("wiki_view.html", project = project, 
                    wikiurl = wikiurl, wikipage = wikipage, wikitext = wikitext)


class EditWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        visitor_p = False if (user and project.user_is_author(user)) else True
        self.render("wiki_edit.html", project = project, disabled_p = visitor_p,
                    wikiurl = wikiurl, wikipage = wikipage)

    def post(self, projectid, wikiurl):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/wiki/edit/' + wikiurl
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        content = self.request.get("content")
        summary = self.request.get("summary")
        wikipage = self.get_wikipage(project, wikiurl)
        have_error = False
        error_message = ''
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
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
                wikipage = WikiPages(url = wikiurl, content = content, parent = project.key)
                self.log_and_put(wikipage, "New instance. ")
            else:
                wikipage.content = content
                self.log_and_put(wikipage, "Changing content." )
            new_revision = WikiRevisions(author = user.key, content = content, summary = summary,
                                         parent = wikipage.key)
            project.put_and_notify(self, new_revision, user)
            html, txt = new_revision.notification_html_and_txt(user, project, wikipage)
            self.add_notifications(category = new_revision.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.wiki_notifications_list,
                                   html = html, txt = txt)
            self.redirect("/%s/wiki/page/%s" % (projectid, wikiurl))
        else:
            self.render("wiki_edit.html", project = project, wikipage = wikipage, disabled_p = visitor_p,
                        wikiurl = wikiurl, wikitext = content, error_message = error_message)


class HistoryWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl):
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        revisions = self.get_revisions(wikipage)
        self.render("wiki_history.html", project = project, 
                    wikiurl = wikiurl, wikipage = wikipage, revisions = revisions)


class RevisionWikiPage(GenericWikiPage):
    def get(self, projectid, wikiurl, rev_id):
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        wikipage = self.get_wikipage(project, wikiurl)
        if not wikipage:
            self.error(404)
            self.render("404.html", info = 'Page "%s" not found in this wiki.' % wikipage.url.replace("_"," ").title())
            return
        revision = self.get_revision(wikipage, rev_id)
        if not revision:
            self.error(404)
            self.render("404.html", info = "Revision %s not found" % rev_id)
            return
        if revision:
            wikitext = re.sub(WIKILINKS_RE, make_sub_repl(projectid), revision.content) 
        else:
            wikitext = ''
        self.render("wiki_revision.html", project = project, 
                    wikiurl = wikiurl, revision = revision, wikitext = wikitext)
