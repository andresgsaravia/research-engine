# Your knowledge database

from generic import *

ARXIV_QUERY_URL = "http://export.arxiv.org/api/query?id_list="
ARXIV_RE = r'^[0-9]{4}\.[0-9]{4}$'

## Data Models ##

# This is a site-wide repository
class KnowledgeItems(db.Model):
    species = db.StringProperty(required = True)
    identifier = db.StringProperty(required = True)
    
# Each of the following classes should have as parent one of KnowledgeItems
class arXiv(db.Model):
    article_id = db.StringProperty(required = True)
    title = db.StringProperty(required = True)
    authors = db.StringListProperty(required = True)
    date = db.DateProperty(required = True)
    abstract = db.TextProperty(required = False)       # Are there articles without abstract?
    link = db.LinkProperty(required = True)

# This is user-specific. Each of these items should have as parent one of KnowledgeItems
class LibraryItems(db.Model):
    user = db.ReferenceProperty(required = True)
    review = db.TextProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)


## Handlers ##

class MainPage(GenericPage):
    def get(self):
        self.write("library's main page.")

class Articles(GenericPage):
    def get(self):
        self.write("Your articles in the knowledge database.")

class BlogPosts(GenericPage):
    def get(self):
        self.write("Your blog posts in the knowledge database.")

class Software(GenericPage):
    def get(self):
        self.write("Your software in the knowledge database.")

class New(GenericPage):
    def get(self):
        username = self.get_username()
        self.render("new_knowledge.html")

    def post(self):
        username = self.get_username()
        if not username: self.redirect("/login")
        species = self.request.get('species')
        identifier = self.request.get('identifier')
        have_error = False
        params = {}

        if species == "arXiv":
            if re.match(ARXIV_RE, identifier):
                logging.debug("DB READ: Checking if there's an existing arXiv article.")
                item = db.GqlQuery("SELECT * FROM arXiv WHERE article_id = :1", identifier).get()
            else:
                params['error'] = "That's not a valid arXiv id."
                have_error = True
                
        elif species == "article":
            pass
        elif species == "software":
            pass
        elif species == "webpage":
            pass
        else:
            logging.error("Unknown species for new KnowledgeItem")
            params['error'] = "There was an error processing your request."
            have_error = True
            
        if have_error:
            self.render("new_knowledge.html", **params)
        else:
            pass
