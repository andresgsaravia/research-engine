# bibliography.py
# Bibliography review for a given project

from generic import *
import projects
import urllib2
from xml.dom import minidom

CROSSREF_QUERY_URL = "http://doi.crossref.org/servlet/query?pid=" + ADMIN_EMAIL + "&format=unixsd&id="

def parse_xml(dom, kind):
    "Returns a dict with the appropiate metadata extracted from the input dom."
    res = {}
    if kind == "article":
        res["title"] = dom.getElementsByTagName("journal_article")[0].getElementsByTagName("title")[0].childNodes[0].nodeValue
        res["journal"] = dom.getElementsByTagName("journal_metadata")[0].getElementsByTagName("full_title")[0].childNodes[0].nodeValue
        res["year"] = dom.getElementsByTagName("journal_issue")[0].getElementsByTagName("year")[0].childNodes[0].nodeValue
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
            res["authors"].append([given_name, surname])
    return res

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
class BiblioComment(ndb.Model):
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
        doi = self.request.get("doi").strip()
        error_message = ''
        if visitor_p:
            have_error = True
            error_message = 'You are not a member of this project.'
        elif not doi:
            have_error = True
            error_message = "Please provide a valid DOI."
        else:
            # Check if already present
            previous = BiblioItems.query(BiblioItems.kind == "article", BiblioItems.identifier == doi).get()
            if previous:
                have_error = True
                error_message = "That item has been already added."
            # Query for the metadata
            query_url = CROSSREF_QUERY_URL + urllib2.quote(doi, '')
            try:
                result = urllib2.urlopen(query_url)
            except urllib2.URLError, e:
                have_error = True
                error_message = e
            try:
                result_dom = minidom.parse(result)
            except:
                have_error = True
                error_message = "There was an error parsing the response metadata."
            # Add to the library
            if have_error:
                self.render("biblio_new.html", project = project, error_message = error_message, doi = doi)
            else:
                metadata = parse_xml(result_dom, "article")
                new_item = BiblioItems(title = metadata["title"],
                                       link = "http://dx.doi.org/%s" % doi,
                                       kind = "article",
                                       identifier = doi,
                                       metadata = metadata,
                                       parent = project.key)
                self.log_and_put(new_item)
                self.log_and_put(project, "Updating last_updated property. ")
                self.redirect("/%s/bibliography/%s" % (projectid, new_item.key.integer_id()))
