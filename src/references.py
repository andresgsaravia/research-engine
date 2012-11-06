# Your knowledge database

from generic import *
from google.appengine.ext.db.metadata import Kind
import urllib2, datetime
import xml.dom.minidom as minidom

ARXIV_QUERY_URL = "http://export.arxiv.org/api/query?id_list="
ARXIV_RE = r'^[0-9]{4}\.[0-9]{4}(v[0-9]+)?$'

CROSSREF_QUERY_URL = "http://doi.crossref.org/servlet/query?pid=crossref%40andresgsaravia.com.mx&format=unixref&id="
DOI_RE = r''


###########################
##   Datastore Objects   ##    
###########################

# Specific knowledge items.
class arXiv(db.Model):
    item_id = db.StringProperty(required = True)
    title = db.StringProperty(required = True)
    authors = db.StringListProperty(required = True)
    date = db.DateTimeProperty(required = True)
    abstract = db.TextProperty(required = False)       # Are there articles without abstract?
    link = db.LinkProperty(required = True)

    def full_render(self):
        return render_str("arXiv_reference_full.html", reference = self)

    def short_render(self):
        authors_string = self.authors[0]
        if len(self.authors) > 1:
            authors_string += "<em> et al.</em>"
        return render_str("arXiv_reference_short.html", reference = self, authors_string = authors_string)

    def edit_render(self):
        params = {'reference' : self, 'authors_string' : ''}
        for author in self.authors:
            params["authors_string"] += (author + "; ")
        params["authors_string"]  = params["authors_string"][:-2]
        params["date_string"] = datetime.datetime.strftime(self.date, "%Y-%m-%d")
        return render_str("arXiv_reference_edit.html", **params)


class PublishedArticles(db.Model):
    item_id = db.StringProperty(required = True)       # DOI
    # Journal
    journal = db.StringProperty(required = True)
    abbrev_journal = db.StringProperty(required = False)
    year = db.IntegerProperty(required = True)
    volume = db.StringProperty(required = False)        # Sometimes there are letters here so it can't be an int.
    issue = db.StringProperty(required = False)         # Could this be an int?
    page = db.StringProperty(required = False)
    # Article
    title = db.StringProperty(required = False)         # Some CrossRef records are mising titles... WTF!
    authors = db.StringListProperty(required = True)    # Must be required=True, however it can default to an empty list.
    abstract = db.TextProperty(required = False)        # Crossref doesn't provide this. Maybe we can fetch it in some other way.
    link = db.LinkProperty(required = True)

    def full_render(self):
        return render_str("article_reference_full.html", reference = self)

    def short_render(self):
        authors_string = self.authors[0]
        if len(self.authors) > 1:
            authors_string += "<em> et al.</em>"
        return render_str("article_reference_short.html", reference = self, authors_string = authors_string)

    def edit_render(self):
        authors_string = ''
        for author in self.authors:
            authors_string += (author + "; ")
        authors_string = authors_string[:-2]
        return render_str("article_reference_edit.html", reference = self, authors_string = authors_string)


class WebPage(db.Model):
    item_id = db.StringProperty(required = True) # Link to webpage
    title = db.StringProperty(required = False)
    authors = db.StringListProperty(required = True) # Must be required=True, however it can default to an empty list.
    summary = db.TextProperty(required = False)

    def full_render(self):
        return render_str("webpage_reference_full.html", reference = self)

    def short_render(self):
        if len(self.authors) > 0:
            authors_string = self.authors[0]
            if len(self.authors) > 1:
                authors_string += "<em> et al.</em>"
        else:
            authors_string = 'Unknown author'
        return render_str("webpage_reference_short.html", reference = self, authors_string = authors_string)

    def edit_render(self):
        authors_string = ''
        for author in self.authors:
            authors_string += (author + "; ")
        authors_string = authors_string[:-2]
        return render_str("webpage_reference_edit.html", reference = self, authors_string = authors_string)


##########################
##   Helper functions   ##
##########################

def nice_bs(string):
    "Replaces \n with whitespace and removes leading and trailing whitespace."
    return string.replace("\n", " ").lstrip().rstrip()


def try_get_nodeValue(tree, node_name):
    try:
        return tree.getElementsByTagName(node_name)[0].childNodes[0].nodeValue
    except:
        return None


def arXiv_metadata(arXiv_id):
    arXiv_id = arXiv_id.split('v')[0]     # For now we remove the version from the query.
    tree = minidom.parseString(urllib2.urlopen(ARXIV_QUERY_URL + arXiv_id).read().replace("\n", " "))
    params = {}
    params["item_id"] = arXiv_id
    params["title"] = tree.getElementsByTagName("entry")[0].getElementsByTagName("title")[0].childNodes[0].nodeValue
    params["authors"] = []
    for author in tree.getElementsByTagName("author"):
        author_name = author.getElementsByTagName("name")[0].childNodes[0].nodeValue
        params["authors"].append(author_name)
    date_string = tree.getElementsByTagName("published")[0].childNodes[0].nodeValue
    params["date"] = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    params["abstract"] = tree.getElementsByTagName("summary")[0].childNodes[0].nodeValue
    params["link"] = tree.getElementsByTagName("entry")[0].getElementsByTagName("id")[0].childNodes[0].nodeValue
    return params


def CrossRef_metadata(doi):
    tree = minidom.parseString(urllib2.urlopen(CROSSREF_QUERY_URL + doi).read().replace("\n", " "))
    params = {}
    params["item_id"] = doi
    # metadata is sometimes missing so I use try-except to fetch it.
    params["journal"] = try_get_nodeValue(tree, "full_title")
    if params["journal"]: params["journal"] = params["journal"].title()
    params["abbrev_journal"] = try_get_nodeValue(tree, "abbrev_title")
    params["year"] = int(try_get_nodeValue(tree, "year"))
    params["volume"] = try_get_nodeValue(tree, "volume")
    params["issue"] = try_get_nodeValue(tree, "issue")
    params["page"] = try_get_nodeValue(tree, "first_page")
    params["title"] = try_get_nodeValue(tree, "title")
    params["authors"] = []
    for author in tree.getElementsByTagName("person_name"):
        given_name = author.getElementsByTagName("given_name")[0].childNodes[0].nodeValue
        surname = author.getElementsByTagName("surname")[0].childNodes[0].nodeValue
        params["authors"].append(given_name + " " + surname)   # To have consistency with arXiv references.
    params["abstract"] = ""
    params["link"] = try_get_nodeValue(tree, "resource")
    return params


def WebPage_metadata(link):
    page = urllib2.urlopen(link).read().replace("\n", "")
    params = {}
    params["item_id"] = link
    params["title"] = page[page.find("<title>") + 7 : page.find("</title>")].decode('ascii','ignore')
    return params

# For the add_new_X functions, X should match the database's name. They must return the reference just added.
def add_new_arXiv(identifier):
    params = arXiv_metadata(identifier)
    new = arXiv(**params)
    logging.debug("DB WRITE: Adding new arXiv article :1", identifier)
    new.put()
    return new


def add_new_PublishedArticles(identifier):
    params = CrossRef_metadata(identifier)
    new = PublishedArticles(**params)
    logging.debug("DB WRITE: Adding a new PublishedArticle with DOI :1", identifier)
    new.put()
    return new


def add_new_WebPage(identifier):
    params = WebPage_metadata(identifier)
    new = WebPage(**params)
    logging.debug("DB WRITE: Adding a new WebPage with link :1", identifier)
    new.put()
    return new


def get_add_reference(species, identifier):
    """Returns a reference of the given species and identifier. If it doesn't exist, create it."""
    if species == "arXiv": db_name = "arXiv"
    elif species == "article": db_name = "PublishedArticles"
    elif species == "webpage": db_name = "WebPage"
    else:
        logging.error("Wrong reference species: %s" % species)
        assert False
    logging.debug("DB READ: Checking if %s reference exists in database." % db_name)
    q = db.GqlQuery("SELECT * FROM %s WHERE item_id = '%s'" % (db_name, identifier)).get()
    if q: return q
    return eval('add_new_%s("%s")' % (db_name, identifier))



#####################
##  Web Handlers   ##
#####################

class ReferencePage(GenericPage):
    def get(self, reference_key):
        user = self.get_user()
        go_back_link = self.request.get("go_back_link")
        params = {}
        params["reference_key"] = reference_key
        params["reference"] = self.get_item_from_key(db.Key(reference_key))
        if not params["reference"]:
            logging.warning("Attempted to fetch a non-existing reference's page; key :1", reference_key)
            self.error(404)
        else:
            if go_back_link: params["go_back_link"] = '<a href="%s">&larr; Go back.</a>' % go_back_link
            self.render("reference.html", **params)


class EditReferencePage(GenericPage):
    def get(self, reference_key):
        reference = self.get_item_from_key(db.Key(reference_key))
        if not reference: 
            logging.warning("Attempted to fetch a non-existing reference's page; key :1", reference_key)
            self.error(404)
        else:
            self.render("reference_edit.html", reference = reference)

    def post(self, reference_key):
        username = self.get_username()
        if not username: self.redirect("/login")
        params = {}
        reference = self.get_item_from_key(db.Key(reference_key))
        if not reference:
            logging.warning("Attempted to fetch a non-existing reference's page; key :1", reference_key)
            self.error(404)
        else:
            kind = reference.kind()
            have_error = False
            params["error"] = ''

            if kind == "arXiv":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get("authors_string")
                params["date"] = self.request.get("date")
                params["abstract"]= self.request.get("abstract")
                params["link"] = self.request.get("link")
                if params["title"]: reference.title = nice_bs(params["title"])
                if params["authors_string"]:
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params["date"]:
                    try:
                        reference.date = datetime.datetime.strptime(nice_bs(params["date"]), "%Y-%m-%d")
                    except ValueError:
                        have_error = True
                        params["error"] += "Please check the date is correct. "
                if params["abstract"]: reference.abstract = nice_bs(params["abstract"])
                if params["link"]: 
                    try:
                        reference.link = nice_bs(params["link"])
                    except db.BadValueError:
                        have_error = True
                        params["error"] += "Please check the Link value is a valid URL. "

            elif kind == "PublishedArticles":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get("authors_string")
                params["year"] = self.request.get("year")
                params["issue"] = self.request.get("issue")
                params["volume"] = self.request.get("volume")
                params["page"] = self.request.get("page")
                params["abstract"] = self.request.get("abstract")
                params["link"] = self.request.get("link")
                if params["title"]: reference.title = nice_bs(params["title"])
                if params["authors_string"]: 
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params["year"]: 
                    try:
                        reference.year = int(nice_bs(params["year"]))
                    except ValueError:
                        have_error = True
                        params["error"] += "Please write Year as a single positive integer."
                if params["issue"]: reference.issue = nice_bs(params["issue"])
                if params["volume"]: reference.volume = nice_bs(params["volume"])
                if params["page"]: reference.page = nice_bs(params["page"])
                if params["abstract"]: reference.abstract = nice_bs(params["abstract"])
                if params["link"]: 
                    try:
                        reference.link = nice_bs(params["link"])
                    except db.BadValueError:
                        have_error = True
                        params["error"] += "Please check the link value is a valid URL. "

            elif kind == "WebPage":
                params["title"] = self.request.get('title')
                params["authors_string"] = self.request.get('authors_string')
                params["summary"] = self.request.get('summary')
                if params['title']: reference.title = nice_bs(params['title'])
                if params["authors_string"]:
                    authors = []
                    for author in params["authors_string"].split(";"):
                        authors.append(nice_bs(author))
                    if authors: reference.authors = authors
                if params['summary']: reference.summary = nice_bs(params['summary'])
            else:
                logging.error("Wrong reference species: %s" % species)
                assert False

            if have_error:
                self.render("reference_edit.html", reference = reference, **params)
            else:
                logging.debug("DB WRITE: Updating %s reference metadata." % kind)
                reference.put()
                self.redirect("/reference/%s" % reference.key())

