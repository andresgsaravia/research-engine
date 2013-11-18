# outreach.py
# All related to public outreach

from google.appengine.ext import ndb
import generic, projects

POSTS_PER_PAGE = 10

###########################
##   Datastore Objects   ##
###########################

# Each one should have a RegisteredUser as parent
class OutreachPosts(ndb.Model):
    title = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    published = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def is_open_p(self):
        return True

    def get_number_of_comments(self):
        return 0

######################
##   Web Handlers   ##
######################

class PostPage(generic.GenericPage):
    def put_and_report(self, item, author):
        self.log_and_put(item)
        u_actv = generic.UserActivities(actv_kind = "Outreach", item = item.key, relative_to = author.key, parent = author.key)
        self.log_and_put(u_actv)

    def get_post(self, author, postid):
        self.log_read(OutreachPosts)
        return OutreachPosts.get_by_id(int(postid), parent = author.key)

    def get_posts_list(self, author, page = 0):
        assert type(page) == int
        self.log_read(OutreachPosts, "Fetching a page with %s results. " % (POSTS_PER_PAGE))
        return OutreachPosts.query(ancestor = author.key).order(-OutreachPosts.published).fetch_page(POSTS_PER_PAGE, offset = POSTS_PER_PAGE * page)


class MainPage(PostPage):
    def get(self, username):
        user = self.get_login_user()
        page_user = self.get_user_by_username(username)
        if not page_user:
            self.render("404.html", info = "User %s not found." % username)
            return
        kw = {"page" : self.request.get("page"),
              "plusone_p" : True}
        try:
            kw["page"] = int(kw["page"])
        except ValueError:
            kw["page"] = 0
        kw["posts"], kw["next_page_cursor"], kw["more_p"] = self.get_posts_list(user, kw["page"])
        self.render("outreach_MainPage.html", page_user = page_user, user = user, **kw)
    

class NewPostPage(PostPage):
    def get(self, username):
        user = self.get_login_user()
        if not user:
            self.redirect("login?goback=/%s/outreach/new_post")
            return
        if not user.username == username:
            self.redirect("/%s/outreach"% username)
            return
        self.render("outreach_new_post.html", user = user)

    def post(self, username):
        user = self.get_login_user()
        if not user.username == username:
            self.redirect("/%s/outreach"% username)
            return
        kw = {"title_value": self.request.get("title"),
              "content_value": self.request.get("content"),
              "error_message" : ''}
        have_error = False
        if not kw["title_value"]:
            have_error = True
            kw["title_error"] = True
            kw["error_message"] = "Please provide a title. "
        if not kw["content_value"]:
            have_error = True
            kw["content_error"] = True
            kw["error_message"] += "You must write some content first. "
        if not have_error:
            new_post = OutreachPosts(title = kw["title_value"], content = kw["content_value"], parent = user.key)
            self.put_and_report(new_post, author = user)
            self.redirect("/%s/outreach/%s" % (username, new_post.key.integer_id()))
        else:
            self.render("outreach_new_post.html", user = user, **kw)


class ViewPostPage(PostPage):
    def render(*a, **kw):
        generic.GenericPage.render(plusone_p = True, *a, **kw)

    def get(self, username, postid):
        page_user = self.get_user_by_username(username)
        if not page_user:
            self.render("404.html", info = "User %s not found. " % username)
            return
        post = self.get_post(page_user, postid)
        if not post:
            self.render("404.html", info = "Post %s not found. " % postid)
            return
        self.render("outreach_view_post.html", page_user = page_user, post = post)


class EditPostPage(PostPage):
    def get(self, username, postid):
        user = self.get_login_user()
        if not user:
            self.redirect("login?goback=/%s/outreach/new_post")
            return
        if not user.username == username:
            self.redirect("/%s/outreach"% username)
            return
        post = self.get_post(user, postid)
        if not post:
            self.render("404.html", info = "Post %s not found. " % postid)
            return
        self.render("outreach_edit_post.html", user = user, postid = postid,
                    title_value = post.title, content_value = post.content)

    def post(self, username, postid):
        user = self.get_login_user()
        if not user.username == username:
            self.redirect("/%s/outreach"% username)
            return
        post = self.get_post(user, postid)
        if not post:
            self.render("404.html", info = "Post %s not found. " % postid)
            return
        kw = {"title_value": self.request.get("title"),
              "content_value": self.request.get("content"),
              "postid" : postid,
              "error_message" : ''}
        have_error = False
        if not kw["title_value"]:
            have_error = True
            kw["title_error"] = True
            kw["error_message"] = "Please provide a title. "
        if not kw["content_value"]:
            have_error = True
            kw["content_error"] = True
            kw["error_message"] += "You must write some content first. "
        if not have_error:
            post.title = kw["title_value"]
            post.content = kw["content_value"]
            self.log_and_put(post)
            self.redirect("/%s/outreach/%s" % (username, postid))
        else:
            self.render("outreach_edit_post.html", user = user, **kw)

