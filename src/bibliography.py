# bibliography.py
# Bibliography review for a given project

import generic, projects, groups
import urllib2
from xml.dom import minidom
from google.appengine.ext import ndb

CROSSREF_QUERY_URL = "http://doi.crossref.org/servlet/query?pid=" + generic.ADMIN_EMAIL + "&format=unixsd&id="
ARXIV_QUERY_URL = "http://export.arxiv.org/api/query?id_list="

def get_dom(identifier, kind):
    error_message = ''
    page = False
    dom = False
    if kind == "article":
        query_url = CROSSREF_QUERY_URL + urllib2.quote(identifier, '')
    elif kind == "arXiv":
        query_url = ARXIV_QUERY_URL + identifier
    else:
        return
    # Fetch the page
    try: 
        page = urllib2.urlopen(query_url)
    except urllib2.URLError, e:
        error_message = e
    except:
        error_message = "There was an unexpected error while fetching the metadata. "
    # Parse the XML with minidom
    if page and not error_message:
        try:
            dom = minidom.parse(page)
        except:
            error_message = "There was an error parsing the metadata results. "
    # Check if the query resolved correctly
    if not error_message:
        if kind == "article":
            status = dom.getElementsByTagName("query")[0].getAttribute("status")
            if status != "resolved":
                error_message = "DOI not found on CrossRef. "
        elif kind == "arXiv":
            if len(dom.getElementsByTagName("entry")[0].getElementsByTagName("title")) == 0:
                error_message = "Entry not found on arXiv."
    return dom, error_message


def parse_xml(dom, kind):
    "Returns a dict with the appropiate metadata extracted from the input dom."
    res = {}
    # Published article retrieved by DOI using CrossRef
    if kind == "article":
        res["title"] = dom.getElementsByTagName("journal_article")[0].getElementsByTagName("title")[0].childNodes[0].nodeValue
        res["publication"] = dom.getElementsByTagName("journal_metadata")[0].getElementsByTagName("full_title")[0].childNodes[0].nodeValue
        res["date"] = dom.getElementsByTagName("journal_issue")[0].getElementsByTagName("year")[0].childNodes[0].nodeValue
        res["authors"] = []
        for a in dom.getElementsByTagName("journal_article")[0].getElementsByTagName("contributors")[0].getElementsByTagName("person_name"):
            try:
                given_name = a.getElementsByTagName("given_name")[0].childNodes[0].nodeValue
            except IndexError:
                given_name = ''
            try:
                surname = a.getElementsByTagName("surname")[0].childNodes[0].nodeValue
            except IndexError:
                surname = ''
            res["authors"].append(given_name + " " + surname)
    # arXiv preprint retrived by its ID using the arXiv's API
    elif kind == "arXiv":
        res["publication"] = "arXiv"
        res["title"] = dom.getElementsByTagName("entry")[0].getElementsByTagName("title")[0].childNodes[0].nodeValue
        res["date"]  = dom.getElementsByTagName("entry")[0].getElementsByTagName("published")[0].childNodes[0].nodeValue
        res["summary"]  = dom.getElementsByTagName("entry")[0].getElementsByTagName("summary")[0].childNodes[0].nodeValue
        res["authors"] = []
        for a in dom.getElementsByTagName("entry")[0].getElementsByTagName("author"):
            res["authors"].append(a.getElementsByTagName("name")[0].childNodes[0].nodeValue)
    return res


def make_link(identifier, kind):
    if kind == "article":
        return "http://dx.doi.org/" + identifier
    elif kind == "arXiv":
        return "http://arxiv.org/abs/" + identifier

###########################
##   Datastore Objects   ##
###########################

# Each BiblioItem should have a Project as parent
class BiblioItems(ndb.Model):
    title = ndb.StringProperty(required = True)
    link = ndb.StringProperty(required = True)
    kind = ndb.StringProperty(required = True)          # article, arXiv, book, etc...
    identifier = ndb.StringProperty(required = True)    # DOI, arXiv id, ISSN, etc...
    added = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    metadata = ndb.JsonProperty(required = True)
    open_p = ndb.BooleanProperty(default = True)

    def get_number_of_comments(self):
        return BiblioComments.query(ancestor = self.key).count()
        
    def is_open_p(self):
        return self.open_p

# Each BiblioComment should have a BiblioItem as parent
class BiblioComments(ndb.Model):
    content = ndb.TextProperty(required = True)
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)

    def is_open_p(self):
        return self.key.parent().get().open_p

######################
##   Web Handlers   ##
######################

class BiblioPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, bibliography_tab_class = "active", *a, **kw)

    def get_BiblioItems_list(self, project):
        self.log_read(BiblioItems, "Fetching all bibliography items for a project. ")
        return BiblioItems.query(ancestor = project.key).order(-BiblioItems.last_updated).fetch()

    def get_item(self, project, itemid, log_message = ''):
        self.log_read(BiblioItems, log_message)
        return BiblioItems.get_by_id(int(itemid), parent = project.key)

    def get_comments_list(self, bibitem):
        self.log_read(BiblioComments, "Fetching all the comments for a bibliographic item. ")
        return BiblioComments.query(ancestor = bibitem.key).order(BiblioComments.date).fetch()

    def get_comment(self, bibitem, commentid):
        self.log_read(BiblioComments)
        return BiblioComments.get_by_id(int(commentid), parent = bibitem.key)

        
class MainPage(BiblioPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        self.render("biblio_main.html", project = project, items = self.get_BiblioItems_list(project),
                    visitor_p = not (user and project.user_is_author(user)))


class NewItemPage(BiblioPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/bibliography/new" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/bibliography" % projectid)
            return
        self.render("biblio_new.html", project = project, open_p = project.default_open_p)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = "/" + projectid + "/bibliographt/new_item"
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/bibliography" % projectid)
            return
        have_error = False
        identifier = self.request.get("identifier").strip()
        kind = self.request.get("kind")
        open_p = self.request.get("open_p") == "True"
        error_message = ''
        if not identifier:
            have_error = True
            error_message = "Please write an appropiate value on the seach field. "
        else:
            # Check if already present
            previous = BiblioItems.query(BiblioItems.kind == kind,
                                         BiblioItems.identifier == identifier,
                                         ancestor = project.key).get()
            if previous:
                have_error = True
                error_message = "That item has been already added."
            else:
                item_dom, error_message = get_dom(identifier, kind)
                if error_message: 
                    have_error = True
                else:
                    metadata = parse_xml(item_dom, kind)
        # Add to the library
        if have_error:
            self.render("biblio_new.html", project = project, error_message = error_message, identifier = identifier, kind = kind)
        else:
            new_item = BiblioItems(title = metadata["title"],
                                   link = make_link(identifier, kind),
                                   kind = kind,
                                   identifier = identifier,
                                   open_p = open_p,
                                   metadata = metadata,
                                   parent = project.key)
            self.put_and_report(new_item, user, project)
            self.redirect("/%s/bibliography/%s" % (projectid, new_item.key.integer_id()))


class ItemPage(BiblioPage):
    def get(self, projectid, itemid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found. " % projectid)
            return
        item = self.get_item(project, itemid)
        if not item:
            self.error(404)
            self.render("404.html", info = "Bibliographt item with key <em>%s</em> not found. " % itemid)
            return
        if not ((item.is_open_p()) or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        self.render("biblio_item.html", project = project, item = item, user = user,
                    comments = self.get_comments_list(item))


    def post(self, projectid, itemid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=" + "/" + projectid + "/bibliography/" + itemid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found. " % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/bibliography/%s" % (projectid, itemid))
            return
        item = self.get_item(project, itemid)
        if not item:
            self.error(404)
            self.render("404.html", info = "Bibliographt item with key <em>%s</em> not found. " % itemid)
            return
        action = self.request.get("action")
        error_message = ''
        if action == "make_comment":
            comment = self.request.get("comment").strip()
            if comment:
                new_comment = BiblioComments(author = user.key,
                                             content = comment,
                                             parent = item.key)
                self.put_and_report(new_comment, user, project, item)
        elif action == "toggle_visibility":
            item.open_p = not item.open_p
            self.log_and_put(item)
        elif action == "edit_comment":
            commentid = self.request.get("commentid")
            comment = self.get_comment(item, commentid)
            content = self.request.get("comment").strip()
            if content and (user.key == comment.author):
                comment.content = content
                self.log_and_put(comment)
        self.redirect("/%s/bibliography/%s" % (projectid, itemid))


class CommentPage(BiblioPage):
    def get(self, projectid, itemid, commentid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        item = self.get_item(project, itemid)
        if not item:
            self.error(404)
            self.render("404.html", info = "Bibliographt item with key <em>%s</em> not found. " % itemid)
            return
        if not (item.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        comment = self.get_comment(item, commentid)
        if not comment:
            self.error(404)
            self.render("404.html", info = "Comment with key <em>%s</em> not found. " % commentid)
            return
        self.render("biblio_comment.html", user = user, project = project, item = item, comment = comment)
