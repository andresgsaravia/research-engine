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

######################
##   Web Handlers   ##
######################

class WritingsListPage(GenericPage):
    def get(self, username, projectname):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project:
            self.error(404)
            self.render("404.html")
            return
        writings = []
        for w in CollaborativeWritings.all().ancestor(project).order("-last_updated").run():
            writings.append(w)
        self.render("writings_list.html", p_author = p_author, project = project, writings = writings)


class NewWritingPage(GenericPage):
    def get(self, username, projectname):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
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

    def post(self, username, project_name):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html")
            return
        project = False
        for p in projects.Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
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



###########################################################
#### EVERTTHING BELOW SHOULD BE REVISED AND/OR REMOVED ####
###########################################################


class EditWritingPage(GenericPage):
    def get(self, project_key, writing_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        writing = self.get_item_from_key_str(writing_key)
        if not writing:
            self.error(404)
            return
        kw = {"error"              : "",
              "submit_button_text" : "Save changes",
              "page_title"         : "Edit writing information",
              "title"              : writing.title,
              "description"        : writing.description,
              "cancel_url"         : "/projects/project/%s/cwriting/%s" % (project_key, writing_key)}
        if not project.user_is_author(user):
            kw["error"] = "You are not an author of this project."
        self.render("writing_description.html", **kw)

    def post(self, project_key, writing_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        writing = self.get_item_from_key_str(writing_key)
        if not writing:
            self.error(404)
            return
        title = self.request.get("title")
        description = self.request.get("description")
        have_error = False
        error = ""
        if not title:
            have_error = True
            error += "Please provide a title. "
        if not description:
            have_error = True
            error += "Please provide a description. "
        if (title == writing.title) and (description == writing.description):
            have_error = True
            error += "There aren't any changes to save. "
        if not project.user_is_author(user):
            have_error = True
            error = "You are not an author of this project. "
        if have_error:
            kw = {"page_title"         : "Edit writing information",
                  "cancel_url"         : "/projects/project/%s/cwriting/%s" % (project_key, writing_key),
                  "submit_button_text" : "Save changes",
                  "title"              : title, 
                  "description"        : description,
                  "error"              : error}
            self.render("writing_description.html", **kw)
        else:
            writing.title = title
            writing.description = description
            self.log_and_put(writing)
            self.redirect("/projects/project/%s/cwriting/%s" % (project_key, writing_key))
                          


class WritingPage(GenericPage):
    def get(self, project_key, writing_key):
        user = self.get_user()
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        writing = self.get_item_from_key_str(writing_key)
        if not writing:
            self.error(404)
            return
        kw = {"project"     : project, 
              "writing"     : writing, 
              "error"       : "", 
              "project_key" : project_key, 
              "writing_key" : writing_key,
              "revisions"   : []}
        if not project.user_is_author(user):
            kw["error"] = "You are not an author of this project, you can't save your changes."
            kw["save_disabled"] = "disabled"
        revisions_query = Revisions.all().ancestor(writing).order("-date")
        for rev in revisions_query.run():
            self.log_read(Revisions)
            kw["revisions"].append(rev)
        self.render("writing.html", **kw)

    def post(self, project_key, writing_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        writing = self.get_item_from_key_str(writing_key)
        if not writing:
            self.error(404)
            return
        content = self.request.get("content")
        kw = {"project"     : project, 
              "writing"     : writing, 
              "error"       : "", 
              "project_key" : project_key, 
              "writing_key" : writing_key,
              "content"     : content, 
              "summary"     : self.request.get("summary")}
        have_error = False
        if not project.user_is_author(user):
            have_error = True
            kw["error"] = "You are not an author of this project, you can't save your changes."
            kw["save_disabled"] = "disabled"
        if not content:
            have_error = True
            kw["error"] = "You must provide some content"
        kw["revisions"] = []
        revisions_query = Revisions.all().ancestor(writing).order("-date")
        for rev in revisions_query.run():
            logging.debug("DB READ: Handler WritingPage is fetching a Revision.")
            kw["revisions"].append(rev)
        if kw["revisions"] and kw["revisions"][0].content == content: 
            have_error = True
            kw["error"] = "There aren't any changes to save."
        if have_error:
            self.render("writing.html", **kw)
        else:
            new_revision = Revisions(author = user.key(), content = content, 
                                     parent = writing, summary = kw["summary"])
            self.log_and_put(new_revision)
            self.redirect("/projects/project/%s/cwriting/view/%s" % (project_key, new_revision.key()))


class ViewRevisionPage(GenericPage):
    def get(self, project_key, revision_key):
        revision = self.get_item_from_key_str(revision_key)
        if not revision:
            self.error(404)
            return
        writing = revision.parent()
        assert writing           # We shouldn't have Revisions without a CollaborativeWriting parent
        self.render("revision.html", revision = revision, writing = writing, project_key = project_key)
