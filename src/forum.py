# forum.py
# For the forums inside each project.

from generic import *
import projects


###########################
##   Datastore Objects   ##
###########################

# Each ForumThread should have a project as parent.
class ForumThreads(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    title = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    started = ndb.DateTimeProperty(auto_now_add = True)
    date = ndb.DateTimeProperty(auto_now = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    open_p = ndb.BooleanProperty(default = True)

    def get_number_of_comments(self):
        return ForumComments.query(ancestor = self.key).count()

    def is_open_p(self):
        return self.open_p

# each ForumComment should have a ForumThread as parent.
class ForumComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def is_open_p(self):
        return self.key.parent().get().open_p


######################
##   Web Handlers   ##
######################

class ForumPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, forum_tab_class = "active", *a, **kw)

    def get_threads(self, project, log_message = ''):
        self.log_read(ForumComments, "Fetching all the thread in a project's forum. ")
        return ForumThreads.query(ancestor = project.key).order(-ForumThreads.last_updated).fetch()

    def get_thread(self, project, thread_id, log_message = ''):
        self.log_read(ForumThreads, log_message)
        return ForumThreads.get_by_id(int(thread_id), parent = project.key)

    def get_comments(self, thread):
        self.log_read(ForumComments, 'Fetching all the comments in a thread. ')
        return ForumComments.query(ancestor = thread.key).order(ForumComments.date).fetch()


class MainPage(ForumPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return            
        self.render("forum_main.html", project = project, user = user, items = self.get_threads(project),
                    visitor_p = not (user and project.user_is_author(user)))


class NewThreadPage(ForumPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/forum/new_thread" % projectid)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/forum" % projectid)
            return
        kw = {"title" : "New forum thread",
              "name_placeholder" : "Brief description of the thread.",
              "content_placeholder" : "Content of your thread.",
              "submit_button_text" : "Create thread",
              "cancel_url" : "/%s/forum" % projectid,
              "more_head" : "<style>#forum-tab {background: white;}</style>",
              "markdown_p" : True,
              "open_choice_p": True,
              "open_p" : project.default_open_p,
              "breadcrumb" : '<li class="active">Forum</li>'}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/forum/new_thread" % projectid)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/forum" % projectid)
            return
        have_error = False
        kw = {"error_message" : '',
              "name_value" : self.request.get("name"),
              "content_value" : self.request.get("content"),
              "open_p": self.request.get("open_p") == "True"}
        if not kw["name_value"]:
            have_error = True
            kw["error_message"] += "Please provide a brief description for this thread. "
            kw["nClass"] = "has-error"
        if not kw["content_value"]:
            have_error = True
            kw["error_message"] += "You need to write some content before publishing this forum thread. "
            kw["cClass"] = "has-error"
        if have_error:
            kw["title"] = "New forum thread"
            kw["name_placeholder"] = "Brief description of the thread. "
            kw["content_placeholder"] = "Content of the thread"
            kw["submit_button_text"] = "Create thread"
            kw["markdown_p"] = True
            kw["open_choice_p"] = True
            kw["cancel_url"] = "/%s/forum" % projectid
            kw["breadcrumb"] = '<li class="active">Forum</li>'
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_thread = ForumThreads(author = user.key, parent = project.key,
                                      title = kw["name_value"], content = kw["content_value"], open_p = kw["open_p"])
            self.put_and_report(new_thread, user, project)
            self.redirect("/%s/forum/%s" % (projectid, new_thread.key.integer_id()))


class ThreadPage(ForumPage):
    def get(self, projectid, thread_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        thread = self.get_thread(project, thread_id)
        if not thread:
            self.error(404)
            self.render("404.html", info = 'Thread with key <em>%s</em> not found' % thread_id)
            return
        if not (thread.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        comments = self.get_comments(thread)
        self.render("forum_thread.html", project = project, user = user, thread = thread, 
                    comments = comments)

    def post(self, projectid, thread_id):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/forum/%s" % (projectid, thread_id))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        thread = self.get_thread(project, thread_id)
        if not thread:
            self.error(404)
            self.render("404.html", info = 'Thread with key <em>%s</em> not found' % thread_id)
            return
        if not (thread.is_open_p() or (user and project.user_is_author(user))):
            self.render("project_page_not_visible.html", project = project, user = user)
            return
        have_error = False
        error_message = ''
        comment = self.request.get("comment")
        if comment:
            new_comment = ForumComments(author = user.key, comment = comment, parent = thread.key)
            self.put_and_report(new_comment, user, project, thread)
        self.redirect("/%s/forum/%s" % (projectid, thread_id))


class EditThreadPage(ForumPage):
    def get(self, projectid, thread_id):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/forum/%s/edit" % (projectid, thread_id))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        thread = self.get_thread(project, thread_id)
        if not thread:
            self.error(404)
            self.render("404.html", info = "Thread with key <em>%s</em> not found" % thread_id)
            return
        if not thread.author == user.key:
            self.redirect("/%s/forum/%s" % (projectid, thread_id))
            return
        kw = {"title" : "Edit forum thread",
              "name_value" : thread.title,
              "content_value" : thread.content,
              "open_p" : thread.open_p,
              "name_placeholder" : "Brief description of the thread.",
              "content_placeholder" : "Content of your thread.",
              "submit_button_text" : "Save changes",
              "cancel_url" : "/%s/forum/%s" % (projectid,thread_id),
              "markdown_p" : True,
              "open_choice_p": True,
              "breadcrumb" : '<li><a href="/%s/forum">Forum</a></li><li class="active">%s</li>' % (projectid, thread.title)}
        self.render("project_form_2.html", user = user, project = project, **kw)

    def post(self, projectid, thread_id):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/forum/%s/edit" % (projectid, thread_id))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        thread = self.get_thread(project, thread_id)
        if not thread:
            self.error(404)
            self.render("404.html", info = "Thread with key <em>%s</em> not found" % thread_id)
            return
        if not thread.author == user.key:
            self.redirect("/%s/forum/%s" % (projectid, thread_id))
            return
        have_error = False
        kw = {"error_message" : '',
              "name_value" : self.request.get("name"),
              "content_value" : self.request.get("content"),
              "open_p" : self.request.get("open_p") == "True"}
        if not kw["name_value"]:
            have_error = True
            kw["error_message"] = "Please provide a brief description for this thread. "
            kw["nClass"] = "has-error"
        if not kw["content_value"]:
            have_error = True
            kw["error_message"] += "You need to write some content before publishing this forum thread. "
            kw["cClass"] = "has-error"
        if have_error:
            kw["title"] = "Edit forum thread"
            kw["name_placeholder"] = "Brief description of the thread."
            kw["content_placeholder"] = "Content of your thread."
            kw["submit_button_text"] = "Save changes"
            kw["cancel_url"] = "/%s/forum/%s" % (projectid,thread_id)
            kw["markdown_p"] = True
            kw["open_choice_p"] = True
            kw["breadcrumb"] = '<li><a href="/%s/forum">Forum</a></li><li class="active">%s</li>' % (projectid, thread.title)
            self.render("project_form_2.html", user = user, project = project, **kw)
        else:
            if (thread.title != kw["name_value"] or thread.content != kw["content_value"] or thread.open_p != kw["open_p"]):
                thread.title = kw["name_value"]
                thread.content = kw["content_value"]
                thread.open_p = kw["open_p"]
                self.log_and_put(thread)
            self.redirect("/%s/forum/%s" % (project.key.integer_id(), thread.key.integer_id()))
