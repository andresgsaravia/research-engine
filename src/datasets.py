# datasets.py
# A module inside each project for uploading and managing datasets

from generic import *
import projects

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


###########################
##   Datastore Objects   ##
###########################

# Each instance should have a Project as parent.
class DataSets(db.Model):
    name = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)


# Should have a DataSet as parent
class DataConcepts(db.Model):
    name = db.StringProperty(required = True)
    description = db.TextProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    last_updated = db.DateTimeProperty(auto_now = True)


# Should have a DataConcept as parent
class DataRevisions(db.Model):
    author = db.ReferenceProperty(required = True)
    date = db.DateTimeProperty(auto_now_add = True)
    meta = db.TextProperty(required = False)
    datafile = blobstore.BlobReferenceProperty(required = True)


######################
##   Web Handlers   ##
######################

class MainPage(GenericPage):
    def get(self, username, projectname):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        datasets = []
        for d in DataSets.all().ancestor(project).order("-last_updated").run():
            datasets.append(d)
        self.render("datasets_main.html", p_author = p_author, project = project, datasets = datasets)


class NewDataSetPage(GenericPage):
    def get(self, username, projectname):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        kw = {"title" : "New dataset",
              "name_placeholder" : "Title of the new dataset",
              "content_placeholder" : "Description of the new dataset",
              "submit_button_text" : "Create dataset",
              "cancel_url" : "/%s/%s/datasets" % (p_author.username, project.name),
              "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a>' % (username, project.name),
              "more_head" : "<style>.datasets-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)


    def post(self, username, project_name):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", project_name.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project:
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        d_name = self.request.get("name")
        d_description = self.request.get("content")
        if not d_name:
            have_error = True
            error_message = "You must provide a name for your new dataset. "
        if not d_description:
            have_error = True
            error_message += "Please provide a description of this dataset. "
        if have_error:
            kw = {"title" : "New dataset",
                  "name_placeholder" : "Title of the new dataset",
                  "content_placeholder" : "Description of the new dataset",
                  "submit_button_text" : "Create dataset",
                  "cancel_url" : "/%s/%s/datasets" % (p_author.username, project.name),
                  "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a>' % (username, project.name),
                  "more_head" : "<style>.datasets-tab {background: white;}</style>",
                  "name_value" : d_name,
                  "content_value" : d_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_dataset = DataSets(name = d_name, 
                                   description = d_description, 
                                   parent  = project.key())
            self.log_and_put(new_dataset)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s" % (user.username, project.name, new_dataset.key().id()))


class DataSetPage(GenericPage):
    def get(self, username, projectname, dataset_id):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        dataconcepts = []
        for d in DataConcepts.all().ancestor(dataset).order("date").run():
            dataconcepts.append(d)
        self.render("dataset_view.html", p_author = p_author, project = project, dataset = dataset, dataconcepts = dataconcepts)


class NewDataConceptPage(GenericPage):
    def get(self, username, projectname, dataset_id):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        kw = {"title" : "New data concept",
              "name_placeholder" : "Title of the new data concept",
              "content_placeholder" : "Description of the new data concept",
              "submit_button_text" : "Create data concept",
              "cancel_url" : "/%s/%s/datasets/%s" % (username, projectname, dataset.key().id()),
              "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a> / <a href="/%s/%s/datasets/%s">%s</a>' 
              % (username, projectname, username, projectname, dataset.key().id(), dataset.name),
              "more_head" : "<style>.datasets-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)


    def post(self, username, projectname, dataset_id):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project:
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        have_error = False
        error_message = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author of this project. "
        d_name = self.request.get("name")
        d_description = self.request.get("content")
        if not d_name:
            have_error = True
            error_message = "You must provide a name for your new data concept. "
        if not d_description:
            have_error = True
            error_message += "Please provide a description of this data concept. "
        if have_error:
            kw = {"title" : "New data concept",
                  "name_placeholder" : "Title of the new data concept",
                  "content_placeholder" : "Description of the new data concept",
                  "submit_button_text" : "Create data concept",
                  "cancel_url" : "/%s/%s/datasets/%s" % (username, projectname, dataset.key().id()),
                  "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a> / <a href="/%s/%s/datasets/%s">%s</a>' 
                  % (username, projectname, username, projectname, dataset.key().id(), dataset.name),
                  "more_head" : "<style>.datasets-tab {background: white;}</style>",
                  "name_value" : d_name,
                  "content_value" : d_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_dataconcept = DataConcepts(name = d_name, 
                                           description = d_description, 
                                           parent  = dataset)
            self.log_and_put(new_dataconcept)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s/%s" % (user.username, project.name, dataset.key().id(), new_dataconcept.key().id()))


class DataConceptPage(GenericPage):
    def get(self, username, projectname, dataset_id, datac_id):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = DataConcepts.get_by_id(int(datac_id), parent = dataset)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        revisions = []
        for rev in DataRevisions.all().ancestor(datac).order("-date").run():
            revisions.append(rev)
        self.render("dataset_concept_view.html", p_author = p_author, project = project, 
                    dataset = dataset, datac = datac, revisions = revisions)


class NewDataRevisionPage(GenericPage):
    def get(self, username, projectname, dataset_id, datac_id):
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = DataConcepts.get_by_id(int(datac_id), parent = dataset)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        upload_url = blobstore.create_upload_url("/%s/%s/datasets/%s/%s/upload" % (p_author.username, projectname, dataset_id, datac_id))
        self.render("dataset_concept_new_revision.html", p_author = p_author, project = project, 
                    dataset = dataset, datac = datac, upload_url = upload_url, mardown_p = True,
                    error_message = self.request.get("error_message"))


class UploadDataRevisionHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self, username, projectname, dataset_id, datac_id):
        user = None
        cookie = self.request.cookies.get("username")
        if cookie: 
            cookie_username = cookie.split("|")[0]
            u = RegisteredUsers.all().filter("username =", cookie_username).get()
            if u: 
                if get_secure_val(cookie, u.salt): user = u
        if not user: 
            self.redirect("/login")
            return
        p_author = RegisteredUsers.all().filter("username =", username).get()
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = False
        for p in projects.Projects.all().filter("name =", projectname.lower()).run():
            if p.user_is_author(p_author):
                project = p
                break
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = DataSets.get_by_id(int(dataset_id), parent = project)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = DataConcepts.get_by_id(int(datac_id), parent = dataset)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        have_error = False
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author for this project. "
        if not datafile:
            have_error = True
            error_message = "You must select a file to upload."
        if have_error:
            self.redirect("/%s/%s/datasets/%s/%s/new?error_message=%s" % (username, projectname, dataset_id, datac_id, error_message))
        else:
            new_revision = DataRevisions(author = user.key(), meta = meta, datafile = datafile[0].key(), parent = datac)
            new_revision.put()
            dataset.put()
            datac.put()
            project.put()
            self.redirect("/%s/%s/datasets/%s/%s" % (username, projectname, dataset_id, datac_id))


class DownloadDataRevisionHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blobkey):
        if not blobstore.get(blobkey):
            self.error("404.html", info = "File not found. ")
        else:
            blob_info = blobstore.BlobInfo.get(blobkey)
            self.send_blob(blob_info, save_as = True)
