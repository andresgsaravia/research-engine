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
        link_posfix = mobject.groups()[0][:-1].strip().replace(" ","_").lower()
    else:
        link_posfix = text.replace(" ", "_").lower()
    return (link_prefix + link_posfix, text)

# Returns a function suitable to use inside a re.sub(...) call to generate
# a valid htlm <a ...> tag inside a wiki.
def make_sub_repl(username, projectname):
    link_prefix = "/%s/%s/wiki/page/" % (username, projectname)
    return lambda x: '<a href="%s">%s</a>' % (link_and_text(x, link_prefix))


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

    def notification_html_and_txt(self, author, project, wikipage):
        kw = {"author" : author, "project" : project, "wikipage" : wikipage, "revision" : self,
              "author_absolute_link" : DOMAIN_PREFIX + "/" + author.username}
        kw["project_absolute_link"] = kw["author_absolute_link"] + "/" + project.name
        kw["wikipage_absolute_link"] = kw["project_absolute_link"] + "/wiki/page/" + wikipage.url
        return (render_str("emails/wiki.html", **kw), render_str("emails/wiki.txt", **kw))


######################
##   Web Handlers   ##
######################

class ViewWikiPage(projects.ProjectPage):
    def get(self, username, projectname, wikiurl):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectname)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectname.replace("_"," ").title())
            return
        wikipage = WikiPages.all().ancestor(project).filter("url =", wikiurl.lower()).get()
        if wikipage: 
            wikitext = re.sub(WIKILINKS_RE, make_sub_repl(username, projectname), wikipage.content) 
        else:
            wikitext = '' 
        self.render("wiki_view.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage, wikitext = wikitext)


class EditWikiPage(projects.ProjectPage):
    def get(self, username, projectname, wikiurl):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectname)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectname.replace("_"," ").title())
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        self.render("wiki_edit.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage)

    def post(self, username, projectname, wikiurl):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/wiki/edit/' + wikiurl
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectname)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectname.replace("_"," ").title())
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
            html, txt = new_revision.notification_html_and_txt(user, project, wikipage)
            self.add_notifications(category = new_revision.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.wiki_notifications_list,
                                   html = html, txt = txt)
            self.redirect("/%s/%s/wiki/page/%s" % (username, projectname, wikiurl))
        else:
            self.render("wiki_edit.html", p_author = p_author, project = project, wikipage = wikipage,
                        wikiurl = wikiurl, wikitext = content, error_message = error_message)


class HistoryWikiPage(projects.ProjectPage):
    def get(self, username, projectname, wikiurl):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectname)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectname.replace("_"," ").title())
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        revisions = []
        if wikipage:
            for rev in WikiRevisions.all().ancestor(wikipage).order("-date").run():
                revisions.append(rev)
        self.render("wiki_history.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, wikipage = wikipage, revisions = revisions)


class RevisionWikiPage(projects.ProjectPage):
    def get(self, username, projectname, wikiurl, rev_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectname)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectname.replace("_", " ").title())
            return
        wikipage = WikiPages.all().ancestor(project).filter("url = ", wikiurl).get()
        if not wikipage:
            self.error(404)
            self.render("404.html", info = 'Page "%s" not found in this wiki.' % wikipage.replace("_"," ").title())
            return
        revision = WikiRevisions.get_by_id(int(rev_id), parent = wikipage)
        if not revision:
            self.error(404)
            self.render("404.html", info = "Revision %s not found" % rev_id)
            return
        self.render("wiki_revision.html", p_author = p_author, project = project, 
                    wikiurl = wikiurl, revision = revision)
