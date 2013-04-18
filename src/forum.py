# forum.py
# For the forums inside each project.

from generic import *
import projects


###########################
##   Datastore Objects   ##
###########################

# Each ForumThread should have a project as parent.
class ForumThreads(db.Model):
    author = db.ReferenceProperty(required = True)
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    started = db.DateTimeProperty(auto_now_add = True)
    date = db.DateTimeProperty(auto_now = True)
    last_updated = db.DateTimeProperty(auto_now = True)


# each ForumComment should have a ForumThread as parent.
class ForumComments(db.Model):
    author = db.ReferenceProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    comment = db.TextProperty(required = True)


######################
##   Web Handlers   ##
######################

class MainPage(projects.ProjectPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = 'User "%s" not found.' % username)
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project "%s" not found.' % projectid.replace("_"," ").title())
            return
        threads = []
        for t in ForumThreads.all().ancestor(project).order("-last_updated").run():
            threads.append(t)
        self.render("forum_main.html", p_author = p_author, project = project, threads = threads)


class NewThreadPage(projects.ProjectPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        kw = {"title" : "New forum thread",
              "name_placeholder" : "Brief description of the thread.",
              "content_placeholder" : "Content of your thread.",
              "submit_button_text" : "Create thread",
              "cancel_url" : "/%s/%s/forum" % (p_author.username, project.key().id()),
              "more_head" : "<style>.forum-tab {background: white;}</style>",
              "markdown_p" : True,
              "title_bar_extra" : '/ <a href="/%s/%s/forum">Forum</a>' % (username, projectid)}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/forum/new_thread'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ''
        t_title = self.request.get("name")
        t_content = self.request.get("content")
        if not t_title:
            have_error = True
            error_message = "Please provide a brief description for this thread. "
        if not t_content:
            have_error = True
            error_message += "You need to write some content before publishing this forum thread. "
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author for this project. "
        if have_error:
            kw = {"title" : "New forum thread",
                  "name_placeholder" : "Brief description of the thread. ",
                  "content_placeholder" : "Content of the thread",
                  "submit_button_text" : "Create thread",
                  "markdown_p" : True,
                  "cancel_url" : "/%s/%s/forum" % (p_author.username, project.key().id()),
                  "more_head" : "<style>.forum-tab {background: white;}</style>",
                  "name_value": t_title, "content_value": t_content, "error_message" : error_message,
                  "title_bar_extra" : '/ <a href="/%s/%s/forum">Forum</a>' % (username, projectid)}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_thread = ForumThreads(author = user.key(), title = t_title, content = t_content, parent = project)
            self.log_and_put(new_thread)
            self.log_and_put(project,  "Updating last_updated property. ")
            self.redirect("/%s/%s/forum/%s" % (user.username, project.key().id(), new_thread.key().id()))


class ThreadPage(projects.ProjectPage):
    def get(self, username, projectid, thread_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        thread = ForumThreads.get_by_id(int(thread_id), parent = project)
        if not thread:
            self.error(404)
            self.render("404.html")
            return
        comments = []
        for c in ForumComments.all().ancestor(thread).order("date").run():
            comments.append(c)
        self.render("forum_thread.html", p_author = p_author, project = project, thread = thread, comments = comments)

    def post(self, username, projectid, thread_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/forum/' + thread_id
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html")
            return
        thread = ForumThreads.get_by_id(int(thread_id), parent = project)
        if not thread:
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ''
        comment = self.request.get("comment")
        if not project.user_is_author(user):
            have_error = True
            erro_message = "You are not an author in this project. "
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = ForumComments(author = user.key(), comment = comment, parent = thread)
            self.log_and_put(new_comment)
            self.log_and_put(thread, "Updating it's last_updated property. ")
            self.log_and_put(project, "Updating it's last_updated property. ")
            comment = ''
        comments = []
        for c in ForumComments.all().ancestor(thread).order("date").run():
            comments.append(c)
        self.render("forum_thread.html", p_author = p_author, project = project, thread = thread, comments = comments,
                    comment = comment, error_message = error_message)
