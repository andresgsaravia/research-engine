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
    open_p = ndb.BooleanProperty(default = True)

    def is_open_p(self):
        return self.open_p

    def get_number_of_comments(self):
        return CodeComments.query(ancestor = self.key).count()


# Each RepositoryComment should have a CodeRepository as parent
class CodeComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def is_open_p(self):
        return self.key.parent().get().open_p


######################
##   Web Handlers   ##
######################

class CodePage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, code_tab_class = "active", *a, **kw)

    def get_codes_list(self, project):
        self.log_read(CodeRepositories, "Fetching all the code reposirtories. ")
        return CodeRepositories.query(ancestor = project.key).order(-CodeRepositories.last_updated).fetch()

    def get_code(self, project, code_id, log_message = ''):
        self.log_read(CodeRepositories, log_message)
        return CodeRepositories.get_by_id(int(code_id), parent = project.key)

    def get_comments(self, code):
        self.log_read(CodeComments, "Fetching all the comments for a code repository. ")
        return CodeComments.query(ancestor = code.key).order(CodeComments.date).fetch()


class CodesListPage(CodePage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        self.render("code_list.html", project = project, 
                    items = self.get_codes_list(project), visitor_p = not (user and project.user_is_author(user)))


class NewCodePage(CodePage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/code" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/code" % projectid)
            return
        kw = {"breadcrumb" : '<li class="active">Source code</li>',
              "title" : "Add a source code repository",
              "name_placeholder" : "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name",
              "content_placeholder" : "Briefly describe how this repository is related to the project.",
              "submit_button_text" : "Add repository",
              "markdown_p" : True,
              "open_choice_p" : True,
              "open_p" : project.default_open_p,
              "cancel_url" : "/%s/code" % projectid}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("\login?goback=/%s/code/new" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/code" % projectid)
            return
        have_error = False
        kw = {"name_value" : self.request.get("name").strip(),
              "content_value" : self.request.get("content"),
              "open_p" : self.request.get("open_p") == "True"}
        if not kw["name_value"]:
            have_error = True
            kw["error_message"] = "Please provide a link to the repository you want to add. "
            kw["nClass"] = "has-error"
        elif not re.match(GITHUB_REPO_RE, kw["name_value"]):
            have_error = True
            kw["error_message"] = "That doesn't look like a valid GitHub url. Please make sure it has the form https://github.com/<em>author-name</em>/<em>repo-name</em>. "
            kw["nClass"] = "has-error"
        if not kw["content_value"]:
            have_error = True
            kw["error_message"] = "Please provide a brief description of the relationship of this repository to the project. "
            kw["cClass"] = "has-error"
        # Fetch the repo
        if not have_error:
            repo_api_url = GITHUB_API_PREFIX + re.split(GITHUB_PREFIX, kw["name_value"])[1]
            repo_fetch = urlfetch.fetch(url = repo_api_url, method = urlfetch.GET, follow_redirects = True)
            if not repo_fetch.status_code == 200:
                have_error = True
                kw["error_message"] = "Could not retrieve url <em>%s</em><br/> Please check the url is correct." % kw["name_value"]
                kw["nClass"] = "has-error"
            # Check for duplicated
            elif CodeRepositories.query(CodeRepositories.link == str(kw["name_value"]), ancestor = project.key).get():
                have_error = True
                kw["error_message"] = "It seems that repository is already in your project. "
                kw["nClass"] = "has-error"
        if have_error:
            kw["breadcrumb"] = '<li class="active">Source code</li>'
            kw["title"] = "Add a source code repository"
            kw["name_placeholder"] = "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name"
            kw["content_placeholder"] = "Briefly describe how this repository is related to the project."
            kw["submit_button_text"] = "Add repository"
            kw["markdown_p"] = True
            kw["open_choice_p"] = True
            kw["cancel_url"] = "/%s/code" % projectid
            self.render("project_form_2.html", project = project, **kw)
        else:
            repo_json = json.loads(repo_fetch.content)
            new_repo = CodeRepositories(link = kw["name_value"], description = kw["content_value"], open_p = kw["open_p"],
                                        parent = project.key, name = repo_json["full_name"], github_json = repo_json)
            self.put_and_report(new_repo, user, project)
            self.redirect("/%s/code/%s" % (projectid, new_repo.key.integer_id()))


class ViewCodePage(CodePage):
    def get(self, projectid, code_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        code = self.get_code(project, code_id)
        if not code:
            self.error(404)
            self.render("404.html", info = 'Code with key <em>%s</em> not found' % code_id)
            return
        if not (code.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        comments = self.get_comments(code)
        self.render("code_view.html", project = project, user = user, code = code, comments = comments)

    def post(self, projectid, code_id):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/code/%s" % (projectid, code_id))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        code = self.get_code(project, code_id)
        if not code:
            self.error(404)
            self.render("404.html", info = 'Code with key <em>%s</em> not found' % code_id)
            return
        action = self.request.get("action")
        if action == "new_comment":
            comment = self.request.get("comment")
            if comment:
                new_comment = CodeComments(author = user.key, comment = comment, parent = code.key)
                self.put_and_report(new_comment, user, project, code)
        elif action == "toggle_visibility":
            code.open_p = not code.open_p
            self.log_and_put(code)
        self.redirect("/%s/code/%s" % (projectid, code_id))
