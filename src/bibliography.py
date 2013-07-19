# bibliography.py
# Bibliography review for a given project

from generic import *
import projects
import urllib2
from xml.dom import minidom

CROSSREF_QUERY_URL = "http://doi.crossref.org/servlet/query?pid=" + ADMIN_EMAIL + "&format=unixsd&id="
ARXIV_QUERY_URL = "http://export.arxiv.org/api/query?id_list="

def get_dom(identifier, kind):
    error_message = ''
    page = False
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
    if page:
        try:
            dom = minidom.parse(page)
        except:
            error_message = "There was an error parsing the metadata results. "
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

# Each BiblioComment should have a BiblioItem as parent
class BiblioComments(ndb.Model):
    content = ndb.TextProperty(required = True)
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)

######################
##   Web Handlers   ##
######################

class BiblioPage(projects.ProjectPage):
    def get_BiblioItems_list(self, project, log_message = ''):
        items = []
        for i in BiblioItems.query(ancestor = project.key).order(-BiblioItems.last_updated).iter():
            self.log_read(BiblioItems, log_message)
            items.append(i)
        return items

    def get_item(self, project, itemid, log_message = ''):
        self.log_read(BiblioItems, log_message)
        return BiblioItems.get_by_id(int(itemid), parent = project.key)

    def get_comments_list(self, bibitem, log_message = ''):
        comments = []
        for c in BiblioComments.query(ancestor = bibitem.key).order(-BiblioComments.date).iter():
            self.log_read(BiblioComments, log_message)
            comments.append(c)
        return comments


class MainPage(BiblioPage):
    def get(self, projectid):
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project with key <em>%s</em> not found." % projectid)
            return
        self.render("biblio_main.html", project = project, items = self.get_BiblioItems_list(project))


class NewItemPage(BiblioPage):
    def get(self, projectid):
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
        self.render("biblio_new.html", 
                    project = project, disabled_p = not project.user_is_author(user))

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
        have_error = False
        visitor_p = not project.user_is_author(user)
        identifier = self.request.get("identifier").strip()
        kind = self.request.get("kind")
        error_message = ''
        if visitor_p:
            have_error = True
            error_message = 'You are not a member of this project.'
        elif not identifier:
            have_error = True
        else:
            # Check if already present
            previous = BiblioItems.query(BiblioItems.kind == kind, BiblioItems.identifier == identifier).get()
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
                self.render("biblio_new.html", project = project, error_message = error_message, doi = doi)
            else:
                new_item = BiblioItems(title = metadata["title"],
                                       link = make_link(identifier, kind),
                                       kind = "article",
                                       identifier = identifier,
                                       metadata = metadata,
                                       parent = project.key)
                self.log_and_put(new_item)
                self.log_and_put(project, "Updating last_updated property. ")
                self.redirect("/%s/bibliography/%s" % (projectid, new_item.key.integer_id()))


class ItemPage(BiblioPage):
    def get(self, projectid, itemid):
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
        user = self.get_login_user()
        self.render("biblio_item.html", project = project, item = item, 
                    disabled_p = not (user and  project.user_is_author(user)),
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
        item = self.get_item(project, itemid)
        if not item:
            self.error(404)
            self.render("404.html", info = "Bibliographt item with key <em>%s</em> not found. " % itemid)
            return
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not a member of this project. "
        comment = self.request.get("comment").strip()
        if not comment:
            have_error = True
            error_message = "You can not make an empty comment."
        if have_error:
            self.render("biblio_item.html", project = project, item = item,
                        disabled_p = not (user and project.user_is_author(user)),
                        comment = self.get_comments_list(item),
                        error_message = error_message)
        else:
            new_comment = BiblioComments(author = user.key,
                                         content = comment,
                                         parent = item.key)
            self.log_and_put(new_comment)
            self.log_and_put(item, "Updating last_updated property. ")
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/bibliography/%s" % (projectid, itemid))
