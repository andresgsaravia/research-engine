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

    def short_render(self, project_key):
        authors_string = self.authors[0]
        if len(self.authors) > 1:
            authors_string += "<em> et al.</em>"
        return render_str("arXiv_reference_short.html", reference = self,
                          authors_string = authors_string, project_key = project_key)

    def edit_render(self, project_key):
        params = {'reference' : self, 'authors_string' : '', 'project_key' : project_key}
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

    def short_render(self, project_key):
        authors_string = self.authors[0]
        if len(self.authors) > 1:
            authors_string += "<em> et al.</em>"
        return render_str("article_reference_short.html", reference = self,
                          authors_string = authors_string, project_key = project_key)

    def edit_render(self, project_key):
        params = {'reference' : self, 'authors_string' : '', 'project_key' : project_key}
        for author in self.authors:
            params['authors_string'] += (author + "; ")
        params['authors_string'] = params['authors_string'][:-2]
        return render_str("article_reference_edit.html", **params)


class WebPage(db.Model):
    item_id = db.StringProperty(required = True) # Link to webpage
    title = db.StringProperty(required = False)
    authors = db.StringListProperty(required = True) # Must be required=True, however it can default to an empty list.
    summary = db.TextProperty(required = False)

    def full_render(self):
        return render_str("webpage_reference_full.html", reference = self)

    def short_render(self, project_key):
        if len(self.authors) > 0:
            authors_string = self.authors[0]
            if len(self.authors) > 1:
                authors_string += "<em> et al.</em>"
        else:
            authors_string = 'Unknown author'
        return render_str("webpage_reference_short.html", reference = self, 
                          authors_string = authors_string, project_key = project_key)

    def edit_render(self, project_key):
        params = {'reference' : self, 'authors_string' : '', 'project_key' : project_key}
        for author in self.authors:
            params['authors_string'] += (author + "; ")
        params['authors_string'] = params['authors_string'][:-2]
        return render_str("webpage_reference_edit.html", **params)


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



