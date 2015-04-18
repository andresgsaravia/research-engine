# images.py
# All related to Images inside a project.

from google.appengine.api import images
from google.appengine.ext import ndb, blobstore
from google.appengine.ext.webapp import blobstore_handlers
import urllib
import generic, projects


###########################
##   Datastore Objects   ##
###########################

# Images have a Project as parent.
class Images(ndb.Model):
    owner = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    title = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = False)
    date = ndb.DateTimeProperty(auto_now_add = True)
    open_p = ndb.BooleanProperty(default = True)
    image_key = ndb.BlobKeyProperty(required = True)

    def is_open_p(self):
        return self.open_p


######################
##   Web Handlers   ##
######################

class ImagesPage(projects.ProjectPage):
    def get_images_list(self, project):
        self.log_read(Images, "Fetching all the images inside a project")
        return Images.query(ancestor = project.key).order(-Images.date).fetch()

    def get_image(self, project, imageid, log_message = ''):
        self.log_read(Images, log_message)
        return Images.get_by_id(int(imageid), parent = project.key)

    def render(*a, **kw):
        projects.ProjectPage.render(images_tab_class = "active", *a, **kw)


class MainPage(ImagesPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        images = self.get_images_list(project)
        self.render("images_main.html", project = project, user = user, images = images) 


class NewImagePage(ImagesPage):
     def get(self, projectid):
         user = self.get_login_user()
         if not user:
             self.redirect("/login?goback=/%s/images/new" % projectid)
             return
         project = self.get_project(projectid)
         if not project: 
             self.error(404)
             self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
             return
         if not project.user_is_author(user):
             self.redirect("/%s/images" % projectid)
             return
         upload_url = blobstore.create_upload_url("/%s/images/new_image" % projectid)
         kw = {"project" : project,
               "open_p" : project.default_open_p,
               "upload_url" : upload_url,
               "image_class" : self.request.get("image_class"),
               "title_class" : self.request.get("title_class"),
               "error_message" : self.request.get("error_message"),
               "action" : "New", "button_text" : "Upload image"}
         self.render("image_upload.html", **kw)

class UploadNewImage(projects.ProjectBlobstoreUpload):
    def post(self,projectid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/%s/images/new" % projectid)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        if not project.user_is_author(user):
            self.redirect("/%s/images" % projectid)
            return
        have_error = False
        kw = {"error_message" : '',
              "i_title" : self.request.get("i_title"),
              "i_description" : self.request.get("i_description"),
              "open_p" : self.request.get("open_p") == "True"}
        image = self.get_uploads("image")
        if not kw["i_title"]:
            have_error = True
            kw["error_message"] = "Provide a title for your new image. "
            kw["title_class"] = "has-error"
        if not image:
            have_error = True
            kw["error_message"] = "Select an image to upload. "
            kw["image_class"] = "has-error"
        if have_error:
            url = "/%s/images/new" % projectid
            url = url + '?' + urllib.urlencode(kw)
            self.redirect(url)
        else:
            new_image = Images(owner = user.key,
                               title = kw["i_title"],
                               description = kw["i_description"],
                               open_p = kw["open_p"],
                               image_key = image[0].key(),
                               parent = project.key)
            self.put_and_report(new_image, user, project)
            self.redirect("/%s/images/%s" % (projectid, new_image.key.integer_id()))

class ViewImagePage(ImagesPage):
    def get(self, projectid, imageid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        image = self.get_image(project, imageid)
        if not image:
            self.error(404)
            self.render("404.html", info = 'Image with key <em>%s</em> not found' % imageid)
            return
        self.render("image.html", user = user, project = project, image = image, image_url = images.get_serving_url(image.image_key))
