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

    def get_number_of_comments(self):
        return ForumComments.query(ancestor = self.key).count()

    def notification_html_and_txt(self, author, project):
        kw = {"author" : author, "project" : project, "thread" : self,
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["thread_absolute_link"] = kw["project_absolute_link"] + "/forum/" + str(self.key.integer_id())
        return (render_str("emails/forum_thread.html", **kw), render_str("emails/forum_thread.txt", **kw))


# each ForumComment should have a ForumThread as parent.
class ForumComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def notification_html_and_txt(self, author, project, thread):
        kw = {"author" : author, "project" : project, "thread" : thread, "comment" : self,
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["thread_absolute_link"] = kw["project_absolute_link"] + "/forum/" + str(self.key.integer_id())
        return (render_str("emails/forum_comment.html", **kw), render_str("emails/forum_comment.txt", **kw))


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
            goback = '/' + projectid + '/forum/new_thread'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = not project.user_is_author(user)
        kw = {"title" : "New forum thread",
              "name_placeholder" : "Brief description of the thread.",
              "content_placeholder" : "Content of your thread.",
              "submit_button_text" : "Create thread",
              "cancel_url" : "/%s/forum" % projectid,
              "more_head" : "<style>#forum-tab {background: white;}</style>",
              "markdown_p" : True,
              "title_bar_extra" : '/ <a href="/%s/forum">Forum</a>' % projectid,
              "disabled_p" : visitor_p,
              "pre_form_message" : '<span style="color:red;">You are not an author in this project.</span>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/forum/new_thread'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        error_message = ''
        t_title = self.request.get("name")
        t_content = self.request.get("content")
        visitor_p = not project.user_is_author(user)
        if visitor_p:
            have_error = True
            error_message = "You are not an author for this project. "
        else:
            if not t_title:
                have_error = True
                error_message = "Please provide a brief description for this thread. "
            if not t_content:
                have_error = True
                error_message += "You need to write some content before publishing this forum thread. "
        if have_error:
            kw = {"title" : "New forum thread",
                  "name_placeholder" : "Brief description of the thread. ",
                  "content_placeholder" : "Content of the thread",
                  "submit_button_text" : "Create thread",
                  "markdown_p" : True,
                  "cancel_url" : "/%s/forum" % projectid,
                  "more_head" : "<style>#forum-tab {background: white;}</style>",
                  "name_value": t_title, "content_value": t_content, "error_message" : error_message,
                  "title_bar_extra" : '/ <a href="/%s/forum">Forum</a>' % projectid,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<span style="color:red;">You are not an author in this project.</span>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_thread = ForumThreads(author = user.key, title = t_title, content = t_content, parent = project.key)
            project.put_and_notify(self, new_thread, user)
            html, txt = new_thread.notification_html_and_txt(user, project)
            self.add_notifications(category = new_thread.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.forum_threads_notifications_list,
                                   html = html, txt = txt)
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
        comments = self.get_comments(thread)
        visitor_p = False if (user and project.user_is_author(user)) else True
        self.render("forum_thread.html", project = project, user = user, thread = thread, 
                    comments = comments, visitor_p = visitor_p)

    def post(self, projectid, thread_id):
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
        thread = self.get_thread(project, thread_id)
        if not thread:
            self.error(404)
            self.render("404.html", info = 'Thread with key <em>%s</em> not found' % thread_id)
            return
        have_error = False
        error_message = ''
        comment = self.request.get("comment")
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            erro_message = "You are not an author in this project. "
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = ForumComments(author = user.key, comment = comment, parent = thread.key)
            project.put_and_notify(self, new_comment, user)
            html, txt = new_comment.notification_html_and_txt(user, project, thread)
            self.add_notifications(category = new_comment.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.forum_posts_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(thread, "Updating last_updated property. ")
            self.redirect("/%s/forum/%s" % (projectid, thread_id))
        else:
            comments = self.get_comments(thread)
            self.render("forum_thread.html", project = project, thread = thread, user = user,
                        comments = comments, visitor_p = visitor_p, comment = comment,
                        error_message = error_message)
