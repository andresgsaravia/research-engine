# collaborative_writing.py

from generic import *
import projects

###########################
##   Datastore Objects   ##
###########################

# Should have a Project as parent
class CollaborativeWritings(ndb.Model):
    title = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)
    status = ndb.StringProperty(required = False)


# Should have as parent a CollaborativeWriting
class WritingRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now = True)
    content = ndb.TextProperty(required = True)
    summary = ndb.TextProperty(required = False)


# Should have as parent a CollaborativeWriting
class WritingComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    comment = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)


######################
##   Web Handlers   ##
######################

class WritingPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, writings_tab_class = "active", *a, **kw)

    def get_writings_list(self, project, log_message = ''):
        writings = []
        for w in CollaborativeWritings.query(ancestor = project.key).order(-CollaborativeWritings.last_updated).iter():
            self.log_read(CollaborativeWritings, log_message)
            writings.append(w)
        return writings

    def get_writing(self, project, writing_id, log_message = ''):
        self.log_read(CollaborativeWritings, log_message)
        return CollaborativeWritings.get_by_id(int(writing_id), parent = project.key)

    def get_last_revision(self, writing, log_message = ''):
        self.log_read(WritingRevisions, log_message)
        return WritingRevisions.query(ancestor = writing.key).order(-WritingRevisions.date).get()

    def get_revision(self, writing, rev_id, log_message = ''):
        self.log_read(WritingRevisions, log_message)
        return WritingRevisions.get_by_id(int(rev_id), parent = writing.key)

    def get_revisions(self, writing, log_message = ''):
        revisions = []
        for r in WritingRevisions.query(ancestor = writing.key).order(-WritingRevisions.date).iter():
            self.log_read(WritingRevisions, log_message)
            revisions.append(r)
        return revisions

    def get_comments(self, writing, log_message = ''):
        comments = []
        for c in WritingComments.query(ancestor = writing.key).order(-WritingComments.date).iter():
            self.log_read(WritingComments, log_message)
            comments.append(c)
        return comments


class WritingsListPage(WritingPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        self.render("writings_list.html", project = project, user = user, items = self.get_writings_list(project),
                    visitor_p = not (user and project.user_is_author(user)))


class NewWritingPage(WritingPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/writings/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = False if project.user_is_author(user) else True
        kw = {"title" : "New collaborative writing",
              "name_placeholder" : "Title of the new writing",
              "content_placeholder" : "Description of the new writing",
              "submit_button_text" : "Create writing",
              "cancel_url" : "/%s/writings" % projectid,
              "breadcrumb" : '<li class="active">Collaborative writings</li>',
              "disabled_p" : True if visitor_p else False,
              "markdown_p" : True,
              "pre_form_message" : '<p class="text-danger">You are not an author in this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/writings/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        error_message = ''
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
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
                  "cancel_url" : "/%s/%s/writings" % projectid,
                  "breadcrumb" : '<li class="active">Collaborative writings</li>',
                  "name_value" : w_name,
                  "content_value" : w_description,
                  "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "markdown_p" : True,
                  "pre_form_message" : '<p class="text-danger">You are not an author in this project.</p>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_writing = CollaborativeWritings(title = w_name,
                                                description = w_description,
                                                status = "In progress",
                                                parent = project.key)
            self.put_and_report(new_writing, user, project)
            self.redirect("/%s/writings/%s" % (project.key.integer_id(), new_writing.key.integer_id()))


class ViewWritingPage(WritingPage):
    def get(self, projectid, writing_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        last_revision = self.get_last_revision(writing)
        self.render("writings_view.html", project = project, writing = writing, last_revision = last_revision, curr_p = True,
                    visitor_p = not (user and project.user_is_author(user)))


class EditWritingPage(WritingPage):
    def get(self, projectid, writing_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        last_revision = self.get_last_revision(writing)
        if last_revision:
            content = last_revision.content
        else:
            content = ''
        visitor_p = False if (user and project.user_is_author(user)) else True
        if user and visitor_p:
            edit_warning = "You are not an author in this project. You can't make changes to this writing."
        elif visitor_p:
            edit_warning = "Please log in to save your changes."
        else:
            edit_warning = ''
        self.render("writings_edit.html", project = project, writing = writing, visitor_p = visitor_p, edit_p = True,
                    content = content, status = writing.status, user = user)

    def post(self, projectid, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/writings/' + writing_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        last_revision = self.get_last_revision(writing)
        content = self.request.get("content")
        status = self.request.get("status")
        summary = self.request.get("summary")
        have_error = False
        error_message = ''
        visitor_p = False if (user and project.user_is_author(user)) else True
        if visitor_p:
            have_error = True
            error_message = "You are not an author of this project. "
        if not content:
            have_error = True
            error_message = "Please write some content before saving. "
        if last_revision and (content == last_revision.content) and (status == writing.status):
            have_error = True
            error_message = "There aren't any changes to save. "
        if have_error:
            self.render("writings_edit.html", project = project, writing = writing, disabled_p = visitor_p, edit_p = True,
                        content = content, status = status, summary = summary, error_message = error_message, user = user)
        else:
            new_revision = WritingRevisions(author = user.key, content = content, summary = summary, parent = writing.key)
            if status: writing.status = status
            self.put_and_report(new_revision, user, project, writing)
            self.redirect("/%s/writings/%s" % (projectid, writing_id))


class HistoryWritingPage(WritingPage):
    def get(self, projectid, writing_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        revisions = self.get_revisions(writing)
        self.render("writings_history.html", project = project, user = user, writing = writing, revisions = revisions, 
                    hist_p = True, visitor_p = not (user and project.user_is_author(user)))


class ViewRevisionPage(WritingPage):
    def get(self, projectid, writing_id, rev_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        revision = self.get_revision(writing, rev_id)
        if not revision:
            self.error(404)
            self.render("404.html", info = "Revision with key <em>%s</em> not found" % rev_id)
            return
        self.render("writings_revision.html", project = project, hist_p = True, user = user, writing = writing,
                    visitor_p = not (user and project.user_is_author(user)), revision = revision)


class DiscussionPage(WritingPage):
    def get(self, projectid, writing_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        comments = self.get_comments(writing)
        visitor_p = False if (user and project.user_is_author(user)) else True
        self.render("writings_discussion.html", project = project, visitor_p = visitor_p, disc_p = True,
                    writing = writing, comments = comments)

    def post(self, projectid, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/writings/' + writing_id + '/discussion'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        have_error = False
        error_message = ""
        comment = self.request.get("comment")
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            error_message = "You are not an author of this project. "
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = WritingComments(author = user.key, comment = comment, parent = writing.key)
            self.put_and_report(new_comment, user, project, writing)
            self.redirect("/%s/writings/%s/discussion" % (projectid, writing_id))
            return
        else:
            comments = self.get_comments(writing)
            self.render("writings_discussion.html", project = project, visitor_p = visitor_p, user = user,
                        writing = writing, comments = comments, comment = comment, disc_p = True,
                        error_message = error_message)


class InfoPage(WritingPage):
    def get(self, projectid, writing_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        self.render("writings_info.html", project = project, writing = writing, visitor_p = visitor_p,
                    title = writing.title, description = writing.description, info_p = True)

    def post(self, projectid, writing_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/writings/' + writing_id + '/info'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        writing = self.get_writing(project, writing_id)
        if not writing:
            self.error(404)
            self.render("404.html", info = 'Writing with key <em>%s</em> not found' % writing_id)
            return
        have_error = False
        kw = {"title" : self.request.get("title"),
              "description" : self.request.get("description"),
              "visitor_p" : False if project.user_is_author(user) else True,
              "info_p": True}
        if kw["visitor_p"]:
            have_error = True
            kw["error_message"] = "You are not an author of this project. "
        if not kw["title"]:
            have_error = True
            kw["error_message"] = "Please provide a title for this writing before saving. "
            kw["tClass"] = "has-error"
        if not kw["description"]:
            have_error = True
            kw["error_message"] = "Please provide a description for this writing before saving. "
            kw["dClass"] = "has-error"
        if (not have_error) and (kw["title"] != writing.title or kw["description"] != writing.description):
            writing.title = kw["title"]
            writing.description = kw["description"]
            self.log_and_put(writing)
            kw["success_message"] = 'Changes saved'
        self.render("writings_info.html", project = project, writing = writing, **kw)
