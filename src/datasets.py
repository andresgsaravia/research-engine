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
class DataSets(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)


# Should have a DataSet as parent
class DataConcepts(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)


# Should have a DataConcept as parent
class DataRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    meta = ndb.TextProperty(required = False)
    datafile = ndb.BlobKeyProperty(required = True)

    def notification_html_and_txt(self, author, project, dataset, datac):
        kw = {"author" : author, "project" : project, "dataset" : dataset,
              "datac" : datac, "rev" : self, 
              "author_absolute_link" : DOMAIN_PREFIX + "/" + author.username}
        kw["project_absolute_link"] = kw["author_absolute_link"] + "/" + str(project.key.integer_id())
        kw["dataset_absolute_link"] = kw["project_absolute_link"] + "/datasets/" + str(dataset.key.integer_id())
        kw["datac_absolute_link"] = kw["dataset_absolute_link"] + "/" + str(datac.key.integer_id())
        return (render_str("emails/datarev.html", **kw), render_str("emails/datarev.txt", **kw))

######################
##   Web Handlers   ##
######################

class DataPage(projects.ProjectPage):
    def get_datasets(self, project, log_message = ''):
        datasets = []
        for d in DataSets.query(ancestor = project.key).order(-DataSets.last_updated).iter():
            self.log_read(DataSets, log_message)
            datasets.append(d)
        return datasets

    def get_dataset(self, project, dataset_id, log_message = ''):
        self.log_read(DataSets, log_message)
        return DataSets.get_by_id(int(dataset_id), parent = project.key)

    def get_dataconcepts(self, dataset, log_message = ''):
        dataconcepts = []
        for d in DataConcepts.query(ancestor = dataset.key).order(-DataConcepts.date).iter():
            self.log_read(DataConcepts, log_message)
            dataconcepts.append(d)
        return dataconcepts

    def get_dataconcept(self, dataset, datac_id, log_message = ''):
        self.log_read(DataConcepts, log_message)
        return DataConcepts.get_by_id(int(datac_id), parent = dataset.key)

    def get_revisions(self, datac, log_message = ''):
        revisions = []
        for r in DataRevisions.query(ancestor = datac.key).order(-DataRevisions.date).iter():
            self.log_read(DataRevisions, log_message)
            revisions.append(r)
        return revisions

    def get_revision(self, datac, rev_id, log_message = ''):
        self.log_read(DataRevisions, log_message)
        return DataRevisions.get_by_id(int(rev_id), parent = datac.key)


class MainPage(DataPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        datasets = self.get_datasets(project)
        self.render("datasets_main.html", p_author = p_author, project = project, datasets = datasets)


class NewDataSetPage(DataPage):
    def get(self, username, projectid):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        kw = {"title" : "New dataset",
              "name_placeholder" : "Title of the new dataset",
              "content_placeholder" : "Description of the new dataset",
              "submit_button_text" : "Create dataset",
              "markdown_p": True,
              "cancel_url" : "/%s/%s/datasets" % (username, projectid),
              "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a>' % (username, projectid),
              "more_head" : "<style>.datasets-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
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
                  "markdown_p": True,
                  "cancel_url" : "/%s/%s/datasets" % (username, projectid),
                  "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a>' % (username, projectid),
                  "more_head" : "<style>.datasets-tab {background: white;}</style>",
                  "name_value" : d_name,
                  "content_value" : d_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_dataset = DataSets(name = d_name,
                                   description = d_description,
                                   parent  = project.key)
            self.log_and_put(new_dataset)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s" % (user.username, project.key.integer_id(), new_dataset.key.integer_id()))


class DataSetPage(DataPage):
    def get(self, username, projectid, dataset_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        dataconcepts = self.get_dataconcepts(dataset)
        self.render("dataset_view.html", p_author = p_author, project = project, dataset = dataset, dataconcepts = dataconcepts)


class EditDataSetPage(DataPage):
    def get(self, username, projectid, dataset_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found.")
            return
        base_url = "/%s/%s/datasets" % (username, projectid)
        kw = {"title" : "Edit dataset",
              "name_placeholder" : "Title of the dataset",
              "content_placeholder" : "Description of the dataset",
              "submit_button_text" : "Save changes",
              "markdown_p": True,
              "cancel_url" : base_url + "/" + dataset_id,
              "title_bar_extra" : '/ <a href="%s">Datasets</a> / <a href="%s">%s</a>' % (base_url, base_url + '/' + dataset_id, dataset.name),
              "more_head" : "<style>.datasets-tab {background: white;}</style>",
              "name_value" : dataset.name,
              "content_value" : dataset.description}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid, dataset_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found.")
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
            error_message = "You must provide a name for your dataset. "
        if not d_description:
            have_error = True
            error_message += "Please provide a description of this dataset. "
        if have_error:
            base_url = "/%s/%s/datasets" % (username, projectid)
            kw = {"title" : "Edit dataset",
                  "name_placeholder" : "Title of the dataset",
                  "content_placeholder" : "Description of the dataset",
                  "submit_button_text" : "Save changes",
                  "markdown_p": True,
                  "cancel_url" : base_url + '/' + dataset_id,
                  "title_bar_extra" : '/ <a href="%s">Datasets</a> / <a href="%s">%s</a>' % (base_url, base_url + '/' + dataset_id, dataset.name),
                  "more_head" : "<style>.datasets-tab {background: white;}</style>",
                  "name_value" : d_name,
                  "content_value" : d_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            if (d_name != dataset.name) or (d_description != dataset.description):
                dataset.name = d_name
                dataset.description = d_description
                self.log_and_put(dataset)
                self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s" % (user.username, project.key.integer_id(), dataset.key.integer_id()))



class NewDataConceptPage(DataPage):
    def get(self, username, projectid, dataset_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        kw = {"title" : "New data concept",
              "name_placeholder" : "Title of the new data concept",
              "content_placeholder" : "Description of the new data concept",
              "submit_button_text" : "Create data concept",
              "markdown_p": True,
              "cancel_url" : "/%s/%s/datasets/%s" % (username, projectid, dataset_id),
              "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a> / <a href="/%s/%s/datasets/%s">%s</a>' 
              % (username, projectid, username, projectid, dataset_id, dataset.name),
              "more_head" : "<style>.datasets-tab {background: white;}</style>"}
        self.render("project_form_2.html", p_author = p_author, project = project, **kw)

    def post(self, username, projectid, dataset_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
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
                  "markdown_p": True,
                  "cancel_url" : "/%s/%s/datasets/%s" % (username, projectid, dataset_id),
                  "title_bar_extra" : '/ <a href="/%s/%s/datasets">Datasets</a> / <a href="/%s/%s/datasets/%s">%s</a>' 
                  % (username, projectid, username, projectid, dataset_id, dataset.name),
                  "more_head" : "<style>.datasets-tab {background: white;}</style>",
                  "name_value" : d_name,
                  "content_value" : d_description,
                  "error_message" : error_message}
            self.render("project_form_2.html", p_author = p_author, project = project, **kw)
        else:
            new_dataconcept = DataConcepts(name = d_name, 
                                           description = d_description, 
                                           parent  = dataset.key)
            self.log_and_put(new_dataconcept)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s/%s" % (user.username, projectid, dataset_id, new_dataconcept.key.integer_id()))


class DataConceptPage(DataPage):
    def get(self, username, projectid, dataset_id, datac_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        revisions = self.get_revisions(datac)
        self.render("dataset_concept_view.html", p_author = p_author, project = project, 
                    dataset = dataset, datac = datac, revisions = revisions)


class EditConceptPage(DataPage):
    def get(self, username, projectid, dataset_id, datac_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        self.render("dataset_concept_edit.html", p_author = p_author, project = project, 
                    dataset = dataset, datac = datac, description = datac.description, name = datac.name)

    def post(self, username, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        d_name = self.request.get("title")
        d_description = self.request.get("description")
        have_error = False
        error_message = ''
        if not d_name:
            have_error = True
            error_message = "You must provide a name for your new data concept. "
        if not d_description:
            have_error = True
            error_message += "Please provide a description of this data concept. "
        if have_error:
            self.render("dataset_concept_edit.html", p_author = p_author, project = project, 
                        dataset = dataset, datac = datac, name = d_name, description = d_description,
                        error_message = error_message)
        else:
            datac.name = d_name
            datac.description = d_description
            self.log_and_put(datac)
            self.redirect("/%s/%s/datasets/%s/%s" % (username, projectid, dataset_id, datac_id) )


class NewDataRevisionPage(DataPage):
    def get(self, username, projectid, dataset_id, datac_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        upload_url = blobstore.create_upload_url("/%s/%s/datasets/%s/%s/upload" % (p_author.username, projectid, dataset_id, datac_id))
        self.render("dataset_concept_new_revision.html", p_author = p_author, project = project, 
                    dataset = dataset, datac = datac, upload_url = upload_url, error_message = self.request.get("error_message"))


class EditRevisionPage(DataPage):
    def get(self, username, projectid, dataset_id, datac_id, rev_id):
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        rev = self.get_revision(datac, rev_id)
        if not rev:
            self.error(404)
            self.render("404.html", info = "Revision %s not found" % rev_id)
            return
        blob_info = blobstore.BlobInfo.get(rev.datafile)
        size = blob_info.size / 1024.0
        cancel_url = '/%s/%s/datasets/%s/%s' % (username, projectid, dataset.key.integer_id(), datac.key.integer_id())
        upload_url = blobstore.create_upload_url("/%s/%s/datasets/%s/%s/update/%s" % (p_author.username, projectid, dataset_id, datac_id, rev_id))
        self.render("dataset_revision_edit.html", p_author = p_author, project = project,
                    dataset = dataset, datac = datac, rev = rev, blob_info = blob_info, size = size,
                    cancel_url = cancel_url, upload_url = upload_url,
                    error_message = self.request.get("error_message"))


class DataSetBlobstoreUpload(GenericBlobstoreUpload):
    def get_project(self, p_author, projectid, log_message = ''):
        self.log_read(projects.Projects, log_message)
        project = projects.Projects.get_by_id(int(projectid))
        if project.user_is_author(p_author): 
            return project
        else:
            return False

    def get_dataset(self, project, dataset_id, log_message = ''):
        self.log_read(DataSets, log_message)
        return DataSets.get_by_id(int(dataset_id), parent = project.key)

    def get_dataconcept(self, dataset, datac_id, log_message = ''):
        self.log_read(DataConcepts, log_message)
        return DataConcepts.get_by_id(int(datac_id), parent = dataset.key)

    def get_datarevision(self, datac, rev_id, log_message = ''):
        self.log_read(DataRevisions, log_message)
        return DataRevisions.get_by_id(int(rev_id), parent = datac.key)



class UploadDataRevisionHandler(DataSetBlobstoreUpload):
    def post(self, username, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        if not user: 
            goback = '/' + username + '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/new'
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
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
            self.redirect("/%s/%s/datasets/%s/%s/new?error_message=%s" % (username, projectid, dataset_id, datac_id, error_message))
        else:
            new_revision = DataRevisions(author = user.key, meta = meta, datafile = datafile[0].key(), parent = datac.key)
            self.log_and_put(new_revision)
            html, txt = new_revision.notification_html_and_txt(user, project, dataset, datac)
            self.add_notifications(category = new_revision.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.datasets_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(dataset, "Updating last_updated property. ")
            self.log_and_put(datac, "Updating last_updated property. ")
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/%s/datasets/%s/%s" % (username, projectid, dataset_id, datac_id))


class DownloadDataRevisionHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blobkey):
        if not blobstore.get(blobkey):
            self.error("404.html", info = "File not found. ")
        else:
            blob_info = blobstore.BlobInfo.get(blobkey)
            self.send_blob(blob_info, save_as = True)


class UpdateDataRevisionHandler(DataSetBlobstoreUpload):
    def post(self, username, projectid, dataset_id, datac_id, rev_id):
        user = self.get_login_user()
        if not user: 
            goback = '/' + username + '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/edit/' + rev_id
            self.redirect("/login?goback=%s" % goback)
            return
        p_author = self.get_user_by_username(username)
        if not p_author:
            self.error(404)
            self.render("404.html", info = "User not found. ")
            return
        project = self.get_project(p_author, projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = "Project not found. ")
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = "Dataset not found. ")
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = "Data concept not found. ")
            return
        rev = self.get_datarevision(datac, rev_id)
        if not rev:
            self.error(404)
            self.render("404.html", info = "Revision not found")
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author for this project. "
            self.redirect("/%s/%s/datasets/%s/%s/new?error_message=%s" % (username, projectid, dataset_id, datac_id, error_message))
        else:
            # Delete previous blob and reference the new one if necessary
            if datafile:
                blobstore.BlobInfo.get(rev.datafile).delete()
                rev.datafile = datafile[0].key()
            if meta != rev.meta: rev.meta = meta
            rev.put()
            self.redirect("/%s/%s/datasets/%s/%s" % (username, projectid, dataset_id, datac_id))
