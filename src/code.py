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

    def notification_html_and_txt(self, author, project):
        kw = {"author" : author, "project" : project, "code" : self,
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["code_absolute_link"] = kw["project_absolute_link"] + "/code/" + str(self.key.integer_id())
        return (render_str("emails/code.html", **kw), render_str("emails/code.txt", **kw))

    def get_number_of_comments(self):
        return CodeComments.query(ancestor = self.key).count()


# Each RepositoryComment should have a CodeRepository as parent
class CodeComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def notification_html_and_txt(self, author, project, code):
        kw = {"author" : author, "project" : project, "code" : code, "comment" : self,
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["code_absolute_link"] = kw["project_absolute_link"] + "/code/" + str(code.key.integer_id())
        return (render_str("emails/code_comment.html", **kw), render_str("emails/code_comment.txt", **kw))


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
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        self.render("code_list.html", project = project, items = self.get_codes_list(project))


class NewCodePage(CodePage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        kw = {"breadcrumb" : '<li class="active">Source code</li>',
              "title" : "Add a source code repository",
              "name_placeholder" : "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name",
              "content_placeholder" : "Briefly describe how this repository is related to the project.",
              "submit_button_text" : "Add repository",
              "markdown_p" : True,
              "cancel_url" : "/%s/code" % projectid,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("\login?goback=/%s" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        kw = {"link" : self.request.get("name").strip(),
              "description" : self.request.get("content"),
              "visitor_p" : False if project.user_is_author(user) else True}
        if kw["visitor_p"]:
            have_error = True
            kw["error_message"] = "You are not an author in this project. "
        else:
            if not kw["link"]:
                have_error = True
                kw["error_message"] = "Please provide a link to the repository you want to add. "
                kw["nClass"] = "has-error"
            elif not re.match(GITHUB_REPO_RE, kw["link"]):
                have_error = True
                kw["error_message"] = "That doesn't look like a valid GitHub url to me. Please make sure it has the form https://github.com/<em>author-name</em>/<em>repo-name</em>. "
                kw["nClass"] = "has-error"
            if not kw["description"]:
                have_error = True
                kw["error_message"] = "Please provide a brief description of the relationship of this repository to the project. "
                kw["cClass"] = "has-error"
        # Fetch the repo
        if not have_error:
            repo_api_url = GITHUB_API_PREFIX + re.split(GITHUB_PREFIX, kw["link"])[1]
            repo_fetch = urlfetch.fetch(url = repo_api_url, method = urlfetch.GET, follow_redirects = True)
            if not repo_fetch.status_code == 200:
                have_error = True
                kw["error_message"] = "Could not retrieve url <em>%s</em><br/> Please check the url is correct." % kw["link"]
                kw["nClass"] = "has-error"
            # Check for duplicated
            elif CodeRepositories.query(CodeRepositories.link == str(kw["link"]), ancestor = project.key).get():
                have_error = True
                kw["error_message"] = "It seems that repository is already in your project. "
                kw["nClass"] = "has-error"
        if have_error:
            kw["title"] = "Add a source code repository"
            kw["name_placeholder"] = "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name"
            kw["content_placeholder"] = "Briefly describe how this repository is related to the project."
            kw["submit_button_text"] = "Add repository"
            kw["markdown_p"] = True
            kw["cancel_url"] = "/%s/code" % projectid
            kw["name_value"] = kw["link"]
            kw["content_value"] = kw["description"]
            kw["disabled_p"] = True if kw["visitor_p"] else False
            kw["pre_form_message"] = '<p class="text-danger">You are not a member of this project.</p>' if kw["visitor_p"] else ""
            self.render("project_form_2.html", project = project, **kw)
        else:
            repo_json = json.loads(repo_fetch.content)
            new_repo = CodeRepositories(link = kw["link"], description = kw["description"], parent = project.key,
                                        name = repo_json["full_name"], github_json = repo_json)
            project.put_and_notify(self, new_repo, user)
            html, txt = new_repo.notification_html_and_txt(user, project)
            self.add_notifications(category = new_repo.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.code_notifications_list,
                                   html = html, txt = txt)
            self.redirect("/%s/code/%s" 
                          % (projectid, new_repo.key.integer_id()))


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
        visitor_p = False if (user and project.user_is_author(user)) else True
        comments = self.get_comments(code)
        self.render("code_view.html", project = project, code = code, comments = comments, disabled_p = visitor_p)

    def post(self, projectid, code_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/forum/' + thread_id
            self.redirect("/login?goback=%s" % goback)
            return
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
        have_error = False
        error_message = ''
        comment = self.request.get("comment")
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            error_message = "You are not an author in this project. "
        elif not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = CodeComments(author = user.key, comment = comment, parent = code.key)
            project.put_and_notify(self, new_comment, user)
            html, txt = new_comment.notification_html_and_txt(user, project, code)
            self.add_notifications(category = new_comment.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.code_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(code, "Updating it's last_updated property. ")
            comment = ''
        comments = self.get_comments(code)
        self.render("code_view.html", project = project, code = code, comments = comments,
                    comment = comment, error_message = error_message)
