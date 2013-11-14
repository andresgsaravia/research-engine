# datasets.py
# A module inside each project for uploading and managing datasets

import generic, projects

from google.appengine.ext import ndb,blobstore
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
    open_p = ndb.BooleanProperty(default = True)

    def get_number_of_concepts(self):
        return DataConcepts.query(ancestor = self.key).count()

    def is_open_p(self):
        return self.open_p


# Should have a DataSet as parent
class DataConcepts(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def get_number_of_revisions(self):
        return DataRevisions.query(ancestor = self.key).count()

    def is_open_p(self):
        return self.key.parent().get().is_open_p()


# Should have a DataConcept as parent
class DataRevisions(ndb.Model):
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    meta = ndb.TextProperty(required = False)
    datafile = ndb.BlobKeyProperty(required = True)

    def is_open_p(self):
        return self.key.parent().get().is_open_p()


######################
##   Web Handlers   ##
######################

class DataPage(projects.ProjectPage):
    def render(self, *a, **kw):
        projects.ProjectPage.render(self, datasets_tab_class = "active", *a, **kw)

    def get_datasets(self, project):
        self.log_read(DataSets, "Fetching all DataSets for a project. ")
        return DataSets.query(ancestor = project.key).order(-DataSets.last_updated).fetch()

    def get_dataset(self, project, datasetid, log_message = ''):
        self.log_read(DataSets, log_message)
        return DataSets.get_by_id(int(datasetid), parent = project.key)

    def get_dataconcepts(self, dataset):        
        self.log_read(DataConcepts, "Fetching all DataConcepts for a DataSet. ")
        return DataConcepts.query(ancestor = dataset.key).order(-DataConcepts.date).fetch()

    def get_dataconcept(self, dataset, datacid, log_message = ''):
        self.log_read(DataConcepts, log_message)
        return DataConcepts.get_by_id(int(datacid), parent = dataset.key)

    def get_revisions(self, datac):
        self.log_read(DataRevisions, "Fetching all DataRevisions for a DataConcept")
        return DataRevisions.query(ancestor = datac.key).order(-DataRevisions.date).fetch()

    def get_revision(self, datac, revid, log_message = ''):
        self.log_read(DataRevisions, log_message)
        return DataRevisions.get_by_id(int(revid), parent = datac.key)


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
        if not project.user_is_author(user):
            self.redirect("/%s" % projectid)
            return
        kw = {"title" : "New dataset",
              "name_placeholder" : "Title of the new dataset",
              "content_placeholder" : "Description of the new dataset",
              "submit_button_text" : "Create dataset",
              "markdown_p": True,
              "cancel_url" : "/%s/datasets" % projectid,
              "breadcrumb" : '<li class="active">Datasets</li>',
              "open_choice_p" : True,
              "open_p" : project.default_open_p}
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
        if not project.user_is_author(user):
            self.redirect("/%s" % projectid)
            return
        have_error = False
        kw = {"error_message" : '',
              "name_value" : self.request.get("name"),
              "content_value" : self.request.get("content"),
              "open_p" : self.request.get("open_p") == "True"}
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
            kw["open_choice_p"] = True
            kw["markdown_p"] = True
            kw["cancel_url"] = "/%s/datasets" % projectid
            kw["breadcrumb"] = '<li class="active">Datasets</li>'
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_dataset = DataSets(name = kw["name_value"],
                                   description = kw["content_value"],
                                   open_p = kw["open_p"],
                                   parent  = project.key)
            self.put_and_report(new_dataset, user, project)
            self.redirect("/%s/datasets/%s" % (project.key.integer_id(), new_dataset.key.integer_id()))


class DataSetPage(DataPage):
    def get(self, projectid, datasetid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return        
        if dataset.is_open_p() or (user and project.user_is_author(user)):
            self.render("dataset_view.html", project = project, dataset = dataset, items = self.get_dataconcepts(dataset))
        else:
            self.render("project_page_not_visible.html", project = project, user = user)


class EditDataSetPage(DataPage):
    def get(self, projectid, datasetid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/new" % (projectid, datasetid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s" % (projectid, datasetid))
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        base_url = "/%s/datasets" % projectid
        kw = {"title" : "Editing dataset <br/><small>%s</small>" % dataset.name,
              "name_placeholder" : "Title of the dataset",
              "content_placeholder" : "Description of the dataset",
              "submit_button_text" : "Save changes",
              "markdown_p": True,
              "open_choice_p" : True,
              "cancel_url" : base_url + "/" + datasetid,
              "breadcrumb" : '<li><a href="%s">Datasets</a></li><li class="active">%s</li>' % (base_url, dataset.name),
              "name_value" : dataset.name,
              "content_value" : dataset.description,
              "open_p" : dataset.open_p}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, datasetid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/new" % (projectid, datasetid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s" % (projectid, datasetid))
            return
        have_error = False
        kw = {"error_message" : '',
              "name_value" : self.request.get("name"),
              "content_value" : self.request.get("content"),
              "open_p" : self.request.get("open_p") == "True"}
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
            kw["open_choice_p"] = True
            kw["cancel_url"] = base_url + '/' + datasetid
            kw["breadcrumb"] = '<li><a href="%s">Datasets</a><li class="active">%s</li>' % (base_url, dataset.name)
            self.render("project_form_2.html", project = project, **kw)
        else:
            if (kw["name_value"] != dataset.name) or (kw["content_value"] != dataset.description) or (kw["open_p"] != dataset.open_p):
                dataset.name = kw["name_value"]
                dataset.description = kw["content_value"]
                dataset.open_p = kw["open_p"]
                self.log_and_put(dataset)
            self.redirect("/%s/datasets/%s" % (project.key.integer_id(), dataset.key.integer_id()))


class NewDataConceptPage(DataPage):
    def get(self, projectid, datasetid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/new_data" % (projectid, datasetid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s" % (projectid, datasetid))
            return
        kw = {"title" : "New data concept<br/><small>%s</small>" % dataset.name,
              "name_placeholder" : "Title of the new data concept",
              "content_placeholder" : "Description of the new data concept",
              "submit_button_text" : "Create data concept",
              "markdown_p": True,
              "cancel_url" : "/%s/datasets/%s" % (projectid, datasetid),
              "breadcrumb" : '<li><a href="/%s/datasets">Datasets</a></li><li class="active">%s</li>' 
              % (projectid, dataset.name)}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, datasetid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/new_data" % (projectid, datasetid))
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s" % (projectid, datasetid))
            return
        have_error = False
        kw = {"error_message" : '',
              "name_value" : self.request.get("name"),
              "content_value" : self.request.get("content")}
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
            kw["cancel_url"] = "/%s/datasets/%s" % (projectid, datasetid)
            kw["breadcrumb"] = '<li><a href="/%s/datasets">Datasets</a><li class="active">%s</li>' % (projectid, dataset.name)
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_dataconcept = DataConcepts(name = kw["name_value"], 
                                           description = kw["content_value"], 
                                           parent  = dataset.key)
            self.put_and_report(new_dataconcept, user, project, dataset)
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, new_dataconcept.key.integer_id()))


class DataConceptPage(DataPage):
    def get(self, projectid, datasetid, datacid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        if dataset.is_open_p() or (user and project.user_is_author(user)):
            revisions = self.get_revisions(datac)
            self.render("dataset_concept_view.html", project = project, rev_p = True,
                        dataset = dataset, datac = datac, revisions = revisions,
                        visitor_p = not (user and project.user_is_author(user)))
        else:
            self.render("project_page_not_visible.html", project = project, user = user)


class EditConceptPage(DataPage):
    def get(self, projectid, datasetid, datacid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/%s/edit" % (projectid, datasetid, datacid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        self.render("dataset_concept_edit.html", project = project, inf_p = True, user = user,
                    dataset = dataset, datac = datac, description = datac.description, name = datac.name)

    def post(self, projectid, datasetid, datacid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/%s/edit" % (projectid, datasetid, datacid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        have_error = False
        kw = {"name" :self.request.get("title"),
              "description" :self.request.get("description"),
              "error_message" : ''}
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
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))


class NewDataRevisionPage(DataPage):
    def get(self, projectid, datasetid, datacid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/%s/new" % (projectid, datasetid, datacid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        upload_url = blobstore.create_upload_url("/%s/datasets/%s/%s/upload" % (projectid, datasetid, datacid))
        self.render("dataset_concept_new_revision.html", project = project, user = user,
                    dataset = dataset, datac = datac, upload_url = upload_url, new_p = True,
                    error_message = self.request.get("error_message"), fClass = self.request.get("fClass"))


class EditRevisionPage(DataPage):
    def get(self, projectid, datasetid, datacid, revid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/%s/edit/%s" % (projectid, datasetid, datacid, revid))
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        rev = self.get_revision(datac, revid)
        if not rev:
            self.error(404)
            self.render("404.html", info = 'Data revision with key <em>%s</em> not found' % revid)
            return
        blob_info = blobstore.BlobInfo.get(rev.datafile)
        size = blob_info.size / 1024.0
        cancel_url = '/%s/datasets/%s/%s' % (projectid, dataset.key.integer_id(), datac.key.integer_id())
        upload_url = blobstore.create_upload_url("/%s/datasets/%s/%s/update/%s"
                                                 % (projectid, datasetid, datacid, revid))
        self.render("dataset_revision_edit.html", project = project, rev_p = True,
                    dataset = dataset, datac = datac, rev = rev, blob_info = blob_info, size = size,
                    cancel_url = cancel_url, upload_url = upload_url,
                    error_message = self.request.get("error_message"))


class DataSetBlobstoreUpload(generic.GenericBlobstoreUpload):
    def get_project(self, projectid, log_message = ''):
        self.log_read(projects.Projects, log_message)
        project = projects.Projects.get_by_id(int(projectid))
        return project

    def get_dataset(self, project, datasetid, log_message = ''):
        self.log_read(DataSets, log_message)
        return DataSets.get_by_id(int(datasetid), parent = project.key)

    def get_dataconcept(self, dataset, datacid, log_message = ''):
        self.log_read(DataConcepts, log_message)
        return DataConcepts.get_by_id(int(datacid), parent = dataset.key)

    def get_datarevision(self, datac, revid, log_message = ''):
        self.log_read(DataRevisions, log_message)
        return DataRevisions.get_by_id(int(revid), parent = datac.key)

    def put_and_report(self, item, author, project, list_of_things_to_update = []):
        self.log_and_put(item)
        # Log user activity
        u_activity = generic.UserActivities(parent = author.key, item = item.key, relative_to = project.key, actv_kind = "Projects")
        self.log_and_put(u_activity)
        # Log project update
        p_update = projects.ProjectUpdates(parent = project.key, author = author.key, item = item.key)
        self.log_and_put(p_update)
        for i in list_of_things_to_update:
            self.log_and_put(i)
        return


class UploadDataRevisionHandler(DataSetBlobstoreUpload):
    def post(self, projectid, datasetid, datacid):
        user = self.get_login_user()
        if not user: 
            self.redirect("/login?goback=/%s/datasets/%s/%s/new" % (projectid, datasetid, datacid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        have_error = False
        fClass = ''
        if not datafile:
            have_error = True
            error_message = "You must select a file to upload."
            fClass = "has-error"
        if have_error:
            self.redirect("/%s/datasets/%s/%s/new?error_message=%s&fClass=%s" % (projectid, datasetid, datacid, error_message, fClass))
        else:
            new_revision = DataRevisions(author = user.key, meta = meta, datafile = datafile[0].key(), parent = datac.key)
            self.put_and_report(new_revision, user, project, [dataset, datac])
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))


class DownloadDataRevisionHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blobkey):
        if not blobstore.get(blobkey):
            self.error("404.html", info = "File not found. ")
        else:
            blob_info = blobstore.BlobInfo.get(blobkey)
            self.send_blob(blob_info, save_as = True)


class UpdateDataRevisionHandler(DataSetBlobstoreUpload):
    def post(self, projectid, datasetid, datacid, revid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/datasets/%s/%s/edit" % (projectid, datasetid, datacid))
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
            return
        dataset = self.get_dataset(project, datasetid)
        if not dataset:
            self.error(404)
            self.render("404.html", info = 'Dataset with key <em>%s</em> not found' % datasetid)
            return
        datac = self.get_dataconcept(dataset, datacid)
        if not datac:
            self.error(404)
            self.render("404.html", info = 'Data concept with key <em>%s</em> not found' % datacid)
            return
        rev = self.get_datarevision(datac, revid)
        if not rev:
            self.error(404)
            self.render("404.html", info = 'Data revision with key <em>%s</em> not found' % datacid)
            return
        meta = self.request.get("meta")
        datafile = self.get_uploads("file")
        # Delete previous blob and reference the new one if necessary
        if datafile:
            blobstore.BlobInfo.get(rev.datafile).delete()
            rev.datafile = datafile[0].key()
        if meta != rev.meta: rev.meta = meta
        rev.put()
        self.redirect("/%s/datasets/%s/%s" % (projectid, datasetid, datacid))
