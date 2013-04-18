# collaborative_writing.py

from generic import *
import projects

###########################
##   Datastore Objects   ##
###########################

# Should have a Project as parent
class CollaborativeWritings(db.Model):
    title = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)
    status = db.StringProperty(required = False)


# Should have as parent a CollaborativeWriting
class Revisions(db.Model):
    author = db.ReferenceProperty(required = True)
    date = db.DateTimeProperty(auto_now = True)
    content = db.TextProperty(required = True)
    summary = db.TextProperty(required = False)

    def notification_html_and_txt(self, author, project, writing):
        kw = {"author" : author, "project" : project, "writing" : writing, "revision" : self,
              "author_absolute_link" : DOMAIN_PREFIX + "/" + author.username}
        kw["project_absolute_link"] = kw["author_absolute_link"] + "/" + project.name
        kw["writing_absolute_link"] = kw["project_absolute_link"] + "/writings/" + str(writing.key().id())
        kw["revision_absolute_link"] = kw["writing_absolute_link"] + "/rev/" + str(self.key().id())
        return (render_str("notifications/writing.html", **kw), render_str("notifications/writing.txt", **kw))


# Should have as parent a CollaborativeWriting
class WritingComments(db.Model):
    author = db.ReferenceProperty(required = True)
    comment = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)


######################
##   Web Handlers   ##
######################

class WritingsListPage(projects.ProjectPage):
    def get(self, username, projectname):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writings = []
        for w in CollaborativeWritings.all().ancestor(project).order("-last_updated").run():
            writings.append(w)
        self.render("writings_list.html", p_author = p_author, project = project, writings = writings)


class NewWritingPage(projects.ProjectPage):
    def get(self, username, projectname):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/writings/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return        
        kw = {"title" : "New collaborative writing",
              "name_placeholder" : "Title of the new writing",
              "content_placeholder" : "Description of the new writing",
              "submit_button_text" : "Create writing",
              "cancel_url" : "/%s/%s/writings" % (p_author.username, project.name),
              "more_head" : "<style>.writings-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectname):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/writings/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        w_name = self.request.get("name")
        w_description = self.request.get("content")
        if not w_name:
            have_error = True
            error_message = "You must provide a name for your new writing. "
        if not w_description:
            have_error = True
            error_message += "Please provide a description of this writing. "
        if have_error:
            kw = {"title" : "New collaborative writing",
                  "name_placeholder" : "Title of the new writing",
                  "content_placeholder" : "Description of the new writing",
                  "submit_button_text" : "Create writing",
                  "cancel_url" : "/%s/%s/writings" % (p_author.username, project.name),
                  "more_head" : "<style>.writings-tab {background: white;}</style>",
                  "name_value" : w_name,
                  "content_value" : w_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_writing = CollaborativeWritings(title = w_name,
                                                description = w_description,
                                                status = "In progress",
                                                parent = project.key())
            self.log_and_put(new_writing)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/writings/%s" % (user.username, project.name, new_writing.key().id()))


class ViewWritingPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        last_revision = Revisions.all().ancestor(writing).order("-date").get()
        self.render("writings_view.html", p_author = p_author, project = project, writing = writing, last_revision = last_revision)


class EditWritingPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        last_revision = Revisions.all().ancestor(writing).order("-date").get()
        if last_revision:
            content = last_revision.content
        else:
            content = ''
        self.render("writings_edit.html", p_author = p_author, project = project, writing = writing, content = content, status = writing.status)

    def post(self, username, projectname, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/writings/' + writing_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        last_revision = Revisions.all().ancestor(writing).order("date").get()
        content = self.request.get("content")
        status = self.request.get("status")
        summary = self.request.get("summary")
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        if not content:
            have_error = True
            error_message = "Please write some content before saving. "
        if last_revision and (content == last_revision.content) and (status == writing.status):
            have_error = True
            error_message = "There aren't any changes to save. "
        if have_error:
            self.render("writings_edit.html", p_author = p_author, project = project, writing = writing, 
                        content = content, status = status, summary = summary, error_message = error_message)
        else:
            new_revision = Revisions(author = user, content = content, summary = summary, parent = writing)
            link = "/%s/%s/writings/%s" % (user.username, projectname, writing_id)
            self.log_and_put(new_revision)
            html, txt = new_revision.notification_html_and_txt(user, project, writing)
            self.add_notifications(category = new_revision.__class__.__name__,
                                   author = user, html = html, txt = txt,
                                   users_to_notify = project.writings_notifications_list)
            if status: writing.status = status
            self.log_and_put(writing, "Updating its last_updated and status property. ")
            self.log_and_put(project, "Updating its last_updated property. ")
            self.redirect(link)


class HistoryWritingPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        revisions = []
        for r in Revisions.all().ancestor(writing).order("-date").run():
            revisions.append(r)
        self.render("writings_history.html", p_author = p_author, project = project, 
                    writing = writing, revisions = revisions)


class ViewRevisionPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id, rev_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        revision = Revisions.get_by_id(int(rev_id), parent = writing)
        if not revision:
            self.error(404)
            self.render("404.html")
            return
        self.render("writings_revision.html", p_author = p_author, project = project,
                    writing = writing, revision = revision)


class DiscussionPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        comments = []
        for c in WritingComments.all().ancestor(writing).order("-date").run():
            comments.append(c)
        self.render("writings_discussion.html", p_author = p_author, project = project,
                    writing = writing, comments = comments)

    def post(self, username, projectname, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/writings/' + writing_id + '/discussion'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ""
        comment = self.request.get("comment")
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = WritingComments(author = user.key(), comment = comment, parent = writing)
            self.log_and_put(new_comment, "New comment. ")
            comment = ''
        comments = []
        for c in WritingComments.all().ancestor(writing).order("-date").run():
            comments.append(c)
        self.render("writings_discussion.html", p_author = p_author, project = project,
                    writing = writing, comments = comments, comment = comment,
                    error_message = error_message)


class InfoPage(projects.ProjectPage):
    def get(self, username, projectname, writing_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        self.render("writings_info.html", p_author = p_author, project = project, writing = writing,
                    title_value = writing.title, description_value = writing.description)

    def post(self, username, projectname, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectname + '/writings/' + writing_id + '/info'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = self.get_project(p_author, projectname)
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writing = CollaborativeWritings.get_by_id(int(writing_id), parent = project)
        if not writing:
            self.error(404)
            self.render("404.html")
            return
        have_error = False
        error_message = ''
        info_message = '' 
        title = self.request.get("title")
        description = self.request.get("description")
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        if not title:
            have_error = True
            error_message = "Please provide a title for this writing before saving. "
        if not description:
            have_error = True
            error_message += "Please provide a description for this writing before saving. "
        if (not have_error) and (title != writing.title or description != writing.description):
            writing.title = title
            writing.description = description
            self.log_and_put(writing)
            info_message = 'Changes saved'
        self.render("writings_info.html", p_author = p_author, project = project, writing = writing,
                    title_value = title, description_value = description, 
                    error_message = error_message, info_message = info_message)
