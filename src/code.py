# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
from google.appengine.api import urlfetch
import projects
import json

GITHUB_REPO_RE = r'^https://github.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$'
GITHUB_PREFIX  = r'https://github.com/'
GITHUB_API_PREFIX = 'https://api.github.com/repos/'

###########################
##   Datastore Objects   ##
###########################

# Each CodeRepository have a Project as parent
class CodeRepositories(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    last_updated = ndb.DateTimeProperty(auto_now_add = True)
    link = ndb.StringProperty(required = True)
    github_json = ndb.JsonProperty()


# Each RepositoryComment should have a CodeRepository as parent
class RepositoryComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)


######################
##   Web Handlers   ##
######################

class CodePage(projects.ProjectPage):
    def get_codes_list(self, project, log_message = ''):
        codes = []
        for c in CodeRepositories.query(ancestor = project.key).order(-CodeRepositories.last_updated).iter():
            logging.debug("DB READ: Handler %s requests an instance of CodeRepositories. %s"
                          % (self.__class__.__name__, log_message))
            codes.append(c)
        return codes

    def get_code(self, project, code_id, log_message = ''):
        logging.debug("DB READ: Handler %s requests an instance of CodeRepositories. %s"
                      % (self.__class__.__name__, log_message))
        return CodeRepositories.get_by_id(int(code_id), parent = project.key)



class CodesListPage(CodePage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found' % project.name)
            return
        codes = self.get_codes_list(project)
        self.render("code_list.html", p_author = p_author, project = project, codes = codes)


class NewCodePage(CodePage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found' % project.name)
            return
        kw = {"title_bar_extra" : '/ <a href="/%s/%s/code">Source code</a>' % (username, projectid),
              "more_head" : "<style>.code-tab {background: white;}</style>",
              "title" : "Add a source code repository",
              "pre_form_message" : 'Here you can add an existing <a href="https://github.com">GitHub</a> repository to your project so you can keep track of it and start a discussion.',
              "name_placeholder" : "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name",
              "content_placeholder" : "Briefly describe how this repository is related to the project.",
              "submit_button_text" : "Add repository",
              "cancel_url" : "/%s/%s/code" % (username, projectid)}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found' % project.name)
            return
        link = self.request.get("name").strip()
        description = self.request.get("content")
        have_error = False
        error_message = ''
        if not link:
            have_error = True
            error_message = "Please provide a link to the repository you want to add. "
        elif not re.match(GITHUB_REPO_RE, link):
            have_error = True
            error_message = "That doesn't look like a valid GitHub url to me. Please make sure it has the form https://github.com/<em>author-name</em>/<em>repo-name</em>"
        if not description:
            have_error = True
            error_message += "Please provide a brief description of the relationship of this repository to the project. "
        # Fetch the repo
        repo_api_url = GITHUB_API_PREFIX + re.split(GITHUB_PREFIX, link)[1]
        repo_fetch = urlfetch.fetch(url = repo_api_url, method = urlfetch.GET, follow_redirects = True)
        if not repo_fetch.status_code == 200:
            have_error = True
            error_message = "Could not retrieve url <em>%s</em><br/> Please check the url is correct" % link
        # Check for duplicated
        elif CodeRepositories.query(CodeRepositories.link == str(link), ancestor = project.key).get():
            have_error = True
            error_message = "It seems that repository is already in your project. "
        if have_error:
            kw = {"title_bar_extra" : '/ <a href="/%s/%s/code">Source code</a>' % (username, projectid),
                  "more_head" : "<style>.code-tab {background: white;}</style>",
                  "title" : "Add a source code repository",
                  "pre_form_message" : 'Here you can add an existing <a href="https://github.com">GitHub</a> repository to your project so you can keep track of it and start a discussion.',
                  "name_placeholder" : "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name",
                  "content_placeholder" : "Briefly describe how this repository is related to the project.",
                  "submit_button_text" : "Add repository",
                  "cancel_url" : "/%s/%s/code" % (username, projectid),
                  "error_message" : error_message,
                  "name_value" : link,
                  "content_value" : description}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            repo_json = json.loads(repo_fetch.content)
            new_repo = CodeRepositories(link = link, description = description, parent = project.key,
                                        name = repo_json["full_name"], github_json = repo_json)
            self.log_and_put(new_repo)
            self.log_and_put(project, "Updating last_updated property")
            self.redirect("/%s/%s/code/%s" 
                          % (username, projectid, new_repo.key.integer_id()))


class ViewCodePage(CodePage):
    def get(self, username, projectid, code_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found' % project.name)
            return
        code = self.get_code(project, code_id)
        self.render("code_view.html", p_author = p_author, project = project, code = code, comments = [])
