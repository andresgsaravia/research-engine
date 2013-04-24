# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
import projects

###########################
##   Datastore Objects   ##
###########################

# Each CodeRepository have a Project as parent
class CodeRepositories(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    last_updated = ndb.DateTimeProperty()


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
        self.render("code_list.html", p_author = p_author, project = project, codes = [])


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
        kw = {"title" : "Add a source code repository",
              "pre_form_message" : 'Here you can add an existing <a href="https://github.com">GitHub</a> repository to your project so you can keep track of it and start a discussion.',
              "name_placeholder" : "Link to GitHub repository. Something of the form https://github.com/author-name/repo-name",
              "content_placeholder" : "Briefly describe how this repository is related to the project.",
              "submit_button_text" : "Add repository",
              "cancel_url" : "/%s/%s/code" % (username, projectid)}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)
