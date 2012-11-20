# collaborative_writing.py

from generic import *


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

    def short_render(self, project_key):
        return render_str("writing_short.html", writing = self, project_key = project_key)


# Should have as parent a CollaborativeWriting
class Revisions(db.Model):
    author = db.ReferenceProperty(required = True)
    date = db.DateTimeProperty(auto_now = True)
    content = db.TextProperty(required = True)
    summary = db.TextProperty(required = False)

######################
##   Web Handlers   ##
######################

class NewWritingPage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if project:
            params = {}
            params["error"] = ''
            params["project_key"] = project_key
            params["submit_button_text"] = "Create new writing"
            params["page_title"] = "New collaborative writing"
            params["cancel_url"] = "/projects/project/%s" % project_key
            if not project.user_is_author(user):
                params["error"] = "You are not an author for this project."
            self.render("writing_description.html", **params)
        else:
            logging.debug("Handler NewWritingPage tryed to fetch a non-existing project")
            self.error(404)

    def post(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            logging.debug("Handler NewWritingPage tryed to fetch a non-existing project")
            self.error(404)
            return
        params = {"project" : project, "project_key" : project_key, "error" : "", 
                  "submit_button_text" : "Create new writing", "page_title" : "New collaborative writing"}
        params["title"] = self.request.get("title")
        params["description"] = self.request.get("description")
        params["cancel_url"] = "/projects/project/%s" % project_key
        have_error = False
        if not project.user_is_author(user):
            have_error = True
            params["error"] = "You are not an author for this project. "
        if not params["title"]:
            have_error = True
            params["error"] += "Please provide a title. "
        if not params["description"]:
            have_error = True
            params["error"] += "Please provide a brief description of the purpose of this new writing. "
        if have_error:
            self.render("writing_description.html", **params)
        else:
            new_writing = CollaborativeWritings(title = params["title"], description = params["description"],
                                               parent = project)
            logging.debug("DB WRITE: Handler NewWritingPage is creating a new CollaborativeWriting")
            new_writing.put()
            self.redirect("/projects/project/%s/cwriting/%s" % (project_key, new_writing.key()))


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
        params = {"project_key" : project_key, "writing_key" : writing_key, "error" : "",
                  "project" : project, "writing" : writing, "submit_button_text" : "Save changes",
                  "page_title" : "Edit writing information"}
        if not project.user_is_author(user):
            params["error"] = "You are not an author of this project."
        params["title"] = writing.title
        params["description"] = writing.description
        params["cancel_url"] = "/projects/project/%s/cwriting/%s" % (project_key, writing_key)
        self.render("writing_description.html", **params)

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
            t_params = {"error" : "", 
                        "page_title" : "Edit writing information",
                        "cancel_url" : "/projects/project/%s/cwriting/%s" % (project_key, writing_key),
                        "submit_button_text" : "Save changes",
                        "title" : title, 
                        "description" : description,
                        "error" : error}
            self.render("writing_description.html", **t_params)
        else:
            writing.title = title
            writing.description = description
            logging.debug("DB WRITE: Handler EditWritingPage is updating a CollaborativeWriting.")
            writing.put()
            self.redirect("/projects/project/%s/cwriting/%s" % (project_key, writing_key))
                          


class WritingPage(GenericPage):
    def get(self, project_key, writing_key):
        user = self.get_user()
        params = {"project_key" : project_key, "writing_key" : writing_key,
                  "info" : self.request.get("info")}
        project = self.get_item_from_key_str(project_key)
        if not project:
            self.error(404)
            return
        writing = self.get_item_from_key_str(writing_key)
        if not writing:
            self.error(404)
            return
        params = {"project" : project, "writing" : writing, "error" : "", 
                  "project_key" : project_key, "writing_key" : writing_key}
        if not project.user_is_author(user):
            params["error"] = "You are not an author of this project, you can't save your changes."
            params["save_disabled"] = "disabled"
        params["revisions"] = []
        revisions_query = Revisions.all().ancestor(writing).order("-date")
        for rev in revisions_query.run():
            logging.debug("DB READ: Handler WritingPage is fetching a Revision.")
            params["revisions"].append(rev)
        self.render("writing.html", **params)

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
        params = {"project" : project, "writing" : writing, "error" : "", 
                  "project_key" : project_key, "writing_key" : writing_key,
                  "content" : content, "summary" : self.request.get("summary")}
        have_error = False
        if not project.user_is_author(user):
            have_error = True
            params["error"] = "You are not an author of this project, you can't save your changes."
            params["save_disabled"] = "disabled"
        if not content:
            have_error = True
            params["error"] = "You must provide some content"
        params["revisions"] = []
        revisions_query = Revisions.all().ancestor(writing).order("-date")
        for rev in revisions_query.run():
            logging.debug("DB READ: Handler WritingPage is fetching a Revision.")
            params["revisions"].append(rev)
        if params["revisions"] and params["revisions"][0].content == content: 
            have_error = True
            params["error"] = "There aren't any changes to save."
        if have_error:
            self.render("writing.html", **params)
        else:
            new_revision = Revisions(author = user.key(), content = content, 
                                     parent = writing, summary = params["summary"])
            logging.debug("DB WRITE: Handler WritingPage is creating a new Revision.")
            new_revision.put()
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
