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

    def get_number_of_concepts(self):
        return DataConcepts.query(ancestor = self.key).count()


# Should have a DataSet as parent
class DataConcepts(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def get_number_of_revisions(self):
        return DataRevisions.query(ancestor = self.key).count()


# Should have a DataConcept as parent
class DataRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    meta = ndb.TextProperty(required = False)
    datafile = ndb.BlobKeyProperty(required = True)

    def notification_html_and_txt(self, author, project, dataset, datac):
        kw = {"author" : author, "project" : project, "dataset" : dataset,
              "datac" : datac, "rev" : self, 
              "author_absolute_link" : APP_URL + "/" + author.username}
        kw["project_absolute_link"] = APP_URL + "/" + str(project.key.integer_id())
        kw["dataset_absolute_link"] = kw["project_absolute_link"] + "/datasets/" + str(dataset.key.integer_id())
        kw["datac_absolute_link"] = kw["dataset_absolute_link"] + "/" + str(datac.key.integer_id())
        return (render_str("emails/datarev.html", **kw), render_str("emails/datarev.txt", **kw))

######################
##   Web Handlers   ##
######################

class DataPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, datasets_tab_class = "active", *a, **kw)

    def get_datasets(self, project):
        self.log_read(DataSets, "Fetching all DataSets for a project. ")
        return DataSets.query(ancestor = project.key).order(-DataSets.last_updated).fetch()

    def get_dataset(self, project, dataset_id, log_message = ''):
        self.log_read(DataSets, log_message)
        return DataSets.get_by_id(int(dataset_id), parent = project.key)

    def get_dataconcepts(self, dataset):        
        self.log_read(DataConcepts, "Fetching all DataConcepts for a DataSet. ")
        return DataConcepts.query(ancestor = dataset.key).order(-DataConcepts.date).fetch()

    def get_dataconcept(self, dataset, datac_id, log_message = ''):
        self.log_read(DataConcepts, log_message)
        return DataConcepts.get_by_id(int(datac_id), parent = dataset.key)

    def get_revisions(self, datac):
        self.log_read(DataRevisions, "Fetching all DataRevisions for a DataConcept")
        return DataRevisions.query(ancestor = datac.key).order(-DataRevisions.date).fetch()

    def get_revision(self, datac, rev_id, log_message = ''):
        self.log_read(DataRevisions, log_message)
        return DataRevisions.get_by_id(int(rev_id), parent = datac.key)


class MainPage(DataPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        self.render("datasets_list.html", project = project, items = self.get_datasets(project),
                    visitor_p = not (user and project.user_is_author(user)))


class NewDataSetPage(DataPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return        
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = False if project.user_is_author(user) else True
        kw = {"title" : "New dataset",
              "name_placeholder" : "Title of the new dataset",
              "content_placeholder" : "Description of the new dataset",
              "submit_button_text" : "Create dataset",
              "markdown_p": True,
              "cancel_url" : "/%s/datasets" % projectid,
              "breadcrumb" : '<li class="active">Datasets</li>',
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        kw = {"error_message" : ''}
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            kw["error_message"] = "You are not an author of this project. "
        else:
            kw["name_value"] = self.request.get("name")
            kw["content_value"] = self.request.get("content")
            if not kw["name_value"]:
                have_error = True
                kw["error_message"] = "You must provide a name for your new dataset. "
                kw["nClass"] = "has-error"
            if not kw["content_value"]:
                have_error = True
                kw["error_message"] += "Please provide a description of this dataset. "
                kw["cClass"] = "has-error"
        if have_error:
            kw["title"] = "New dataset"
            kw["name_placeholder"] = "Title of the new dataset"
            kw["content_placeholder"] = "Description of the new dataset"
            kw["submit_button_text"] = "Create dataset"
            kw["markdown_p"] = True
            kw["cancel_url"] = "/%s/datasets" % projectid
            kw["breadcrumb"] = '<li>Datasets</li>'
            kw["disabled_p"] = True if visitor_p else False
            kw["pre_form_message"] = '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_dataset = DataSets(name = kw["name_value"],
                                   description = kw["content_value"],
                                   parent  = project.key)
            project.put_and_notify(self, new_dataset, user)
            self.redirect("/%s/datasets/%s" % (project.key.integer_id(), new_dataset.key.integer_id()))


class DataSetPage(DataPage):
    def get(self, projectid, dataset_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return        
        self.render("dataset_view.html", project = project, dataset = dataset, items = self.get_dataconcepts(dataset),
                    visitor_p = not (user and project.user_is_author(user)))


class EditDataSetPage(DataPage):
    def get(self, projectid, dataset_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        base_url = "/%s/datasets" % projectid
        kw = {"title" : "Editing dataset <br/><small>%s</small>" % dataset.name,
              "name_placeholder" : "Title of the dataset",
              "content_placeholder" : "Description of the dataset",
              "submit_button_text" : "Save changes",
              "markdown_p": True,
              "cancel_url" : base_url + "/" + dataset_id,
              "breadcrumb" : '<li><a href="%s">Datasets</a></li><li class="active">%s</li>' % (base_url, dataset.name),
              "name_value" : dataset.name,
              "content_value" : dataset.description,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, dataset_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        have_error = False
        kw = {"error_message" : '',
              "visitor_p" : False if project.user_is_author(user) else True}
        if kw["visitor_p"]:
            have_error = True
            kw["error_message"] = "You are not an author of this project. "
        else:
            kw["name_value"] = self.request.get("name")
            kw["content_value"] = self.request.get("content")
            if not kw["name_value"]:
                have_error = True
                kw["error_message"] = "You must provide a name for your dataset. "
                kw["nClass"] = "has-error"
            if not kw["content_value"]:
                have_error = True
                kw["error_message"] += "Please provide a description of this dataset. "
                kw["cClass"] = "has-error"
        if have_error:
            base_url = "/%s/datasets" % projectid
            kw["title"]  = "Editing dataset <br/><small>%s</small>" % dataset.name
            kw["name_placeholder"] = "Title of the dataset"
            kw["content_placeholder"] = "Description of the dataset"
            kw["submit_button_text"] = "Save changes"
            kw["markdown_p"] = True
            kw["cancel_url"] = base_url + '/' + dataset_id
            kw["breadcrumb"] = '<li><a href="%s">Datasets</a><li class="active">%s</li>' % (base_url, dataset.name)
            kw["disabled_p"] = True if kw["visitor_p"] else False
            kw["pre_form_message"] = '<p class="text-danger">You are not a member of this project.</p>' if kw["visitor_p"] else ""
            self.render("project_form_2.html", project = project, **kw)
        else:
            if (kw["name_value"] != dataset.name) or (kw["content_value"] != dataset.description):
                dataset.name = kw["name_value"]
                dataset.description = kw["content_value"]
                self.log_and_put(dataset)
                self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/datasets/%s" % (project.key.integer_id(), dataset.key.integer_id()))



class NewDataConceptPage(DataPage):
    def get(self, projectid, dataset_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        kw = {"title" : "New data concept<br/><small>%s</small>" % dataset.name,
              "name_placeholder" : "Title of the new data concept",
              "content_placeholder" : "Description of the new data concept",
              "submit_button_text" : "Create data concept",
              "markdown_p": True,
              "cancel_url" : "/%s/datasets/%s" % (projectid, dataset_id),
              "breadcrumb" : '<li><a href="/%s/datasets">Datasets</a></li><li class="active">%s</li>' 
              % (projectid, dataset.name),
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, dataset_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/datasets/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        have_error = False
        kw = {"error_message" : ''}
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            kw["error_message"] = "You are not an author of this project. "
        else:
            kw["name_value"] = self.request.get("name")
            kw["content_value"] = self.request.get("content")
            if not kw["name_value"]:
                have_error = True
                kw["error_message"] = "You must provide a name for your new data concept. "
                kw["nClass"] = "has-error"
            if not kw["content_value"]:
                have_error = True
                kw["error_message"] += "Please provide a description of this data concept. "
                kw["cClass"] = "has-error"
        if have_error:
            kw["title"] = "New data concept<br/><small>%s</small>" % dataset.name
            kw["name_placeholder"] = "Title of the new data concept"
            kw["content_placeholder"] = "Description of the new data concept"
            kw["submit_button_text"] = "Create data concept"
            kw["markdown_p"] = True
            kw["cancel_url"] = "/%s/datasets/%s" % (projectid, dataset_id)
            kw["breadcrumb"] = '<li><a href="/%s/datasets">Datasets</a><li class="active">%s</li>' % (projectid, dataset.name)
            kw["disabled_p"] = True if visitor_p else False
            kw["pre_form_message"] = '<p class="text-danger">You are not a member of this project.</p>' if visitor_p else ""
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_dataconcept = DataConcepts(name = kw["name_value"], 
                                           description = kw["content_value"], 
                                           parent  = dataset.key)
            project.put_and_notify(self, new_dataconcept, user)
            self.redirect("/%s/datasets/%s/%s" % (projectid, dataset_id, new_dataconcept.key.integer_id()))


class DataConceptPage(DataPage):
    def get(self, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        revisions = self.get_revisions(datac)
        self.render("dataset_concept_view.html", project = project, rev_p = True,
                    dataset = dataset, datac = datac, revisions = revisions,
                    visitor_p = not (user and project.user_is_author(user)))


class EditConceptPage(DataPage):
    def get(self, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        self.render("dataset_concept_edit.html", project = project, visitor_p = visitor_p, inf_p = True, user = user,
                    dataset = dataset, datac = datac, description = datac.description, name = datac.name)

    def post(self, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        kw = {"name" :self.request.get("title"),
              "description" :self.request.get("description"),
              "error_message" : '',
              "visitor_p" : False if project.user_is_author(user) else True}
        have_error = False
        if kw["visitor_p"]:
            have_error = True
            kw["error_message"] = "You are not an author of this project."
        else:
            if not kw["name"]:
                have_error = True
                kw["error_message"] = "You must provide a name for your new data concept. "
                kw["nClass"] = "has-error"
            if not kw["description"]:
                have_error = True
                kw["error_message"] += "Please provide a description of this data concept. "
                kw["cClass"] = "has-error"
        if have_error:
            self.render("dataset_concept_edit.html", project = project, user = user, inf_p = True,
                        dataset = dataset, datac = datac, **kw)
        else:
            datac.name = kw["name"]
            datac.description = kw["description"]
            self.log_and_put(datac)
            self.redirect("/%s/datasets/%s/%s" % (projectid, dataset_id, datac_id))


class NewDataRevisionPage(DataPage):
    def get(self, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        upload_url = blobstore.create_upload_url("/%s/datasets/%s/%s/upload" 
                                                 % (projectid, dataset_id, datac_id)) if not visitor_p else ''
        self.render("dataset_concept_new_revision.html", project = project, visitor_p = visitor_p, user = user,
                    dataset = dataset, datac = datac, upload_url = upload_url, new_p = True,
                    error_message = self.request.get("error_message"), fClass = self.request.get("fClass"))


class EditRevisionPage(DataPage):
    def get(self, projectid, dataset_id, datac_id, rev_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        rev = self.get_revision(datac, rev_id)
        if not rev:
            self.error(404)
            self.render("404.html", info = 'Data revision with key <em>%s</em> not found' % rev_id)
            return
        visitor_p = False if (user and project.user_is_author(user)) else True
        blob_info = blobstore.BlobInfo.get(rev.datafile)
        size = blob_info.size / 1024.0
        cancel_url = '/%s/datasets/%s/%s' % (projectid, dataset.key.integer_id(), datac.key.integer_id())
        upload_url = blobstore.create_upload_url("/%s/datasets/%s/%s/update/%s"
                                                 % (projectid, dataset_id, datac_id, rev_id)) if not visitor_p else ''
        self.render("dataset_revision_edit.html", project = project, disabled_p = visitor_p, rev_p = True,
                    dataset = dataset, datac = datac, rev = rev, blob_info = blob_info, size = size,
                    cancel_url = cancel_url, upload_url = upload_url,
                    error_message = self.request.get("error_message"))


class DataSetBlobstoreUpload(GenericBlobstoreUpload):
    def get_project(self, projectid, log_message = ''):
        self.log_read(projects.Projects, log_message)
        project = projects.Projects.get_by_id(int(projectid))
        return project

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
    def post(self, projectid, dataset_id, datac_id):
        user = self.get_login_user()
        if not user: 
            goback = '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        have_error = False
        fClass = ''
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author for this project. "
        if not datafile:
            have_error = True
            error_message = "You must select a file to upload."
            fClass = "has-error"
        if have_error:
            self.redirect("/%s/datasets/%s/%s/new?error_message=%s&fClass=%s" % (projectid, dataset_id, datac_id, error_message, fClass))
        else:
            new_revision = DataRevisions(author = user.key, meta = meta, datafile = datafile[0].key(), parent = datac.key)
            project.put_and_notify(self, new_revision, user)
            html, txt = new_revision.notification_html_and_txt(user, project, dataset, datac)
            self.add_notifications(category = new_revision.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.datasets_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(dataset, "Updating last_updated property. ")
            self.log_and_put(datac, "Updating last_updated property. ")
            self.redirect("/%s/datasets/%s/%s" % (projectid, dataset_id, datac_id))


class DownloadDataRevisionHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blobkey):
        if not blobstore.get(blobkey):
            self.error("404.html", info = "File not found. ")
        else:
            blob_info = blobstore.BlobInfo.get(blobkey)
            self.send_blob(blob_info, save_as = True)


class UpdateDataRevisionHandler(DataSetBlobstoreUpload):
    def post(self, projectid, dataset_id, datac_id, rev_id):
        user = self.get_login_user()
        if not user: 
            goback = '/' + projectid + '/datasets/' + dataset_id + '/' + datac_id + '/edit/' + rev_id
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, dataset_id)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % dataset_id)
            return
        datac = self.get_dataconcept(dataset, datac_id)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datac_id)
            return
        rev = self.get_datarevision(datac, rev_id)
        if not rev:
            self.error(404)
            self.render("404.html", info = 'Data revision with key <em>%s</em> not found' % datac_id)
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        if not project.user_is_author(user):
            have_error = True
            error_message = "You are not an author for this project. "
            self.redirect("/%s/datasets/%s/%s/new?error_message=%s" % (projectid, dataset_id, datac_id, error_message))
        else:
            # Delete previous blob and reference the new one if necessary
            if datafile:
                blobstore.BlobInfo.get(rev.datafile).delete()
                rev.datafile = datafile[0].key()
            if meta != rev.meta: rev.meta = meta
            rev.put()
            self.redirect("/%s/datasets/%s/%s" % (projectid, dataset_id, datac_id))
