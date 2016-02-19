# groups.py
# For creating, managing and updating groups.

from google.appengine.ext import ndb
import generic, email_messages

UPDATES_TO_DISPLAY = 30           # number of updates to display in the Overview tab


###########################
##   Datastore Objects   ##
###########################

class Groups(ndb.Model):
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = False)
    members = ndb.KeyProperty(repeated = True)
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def list_of_members(self, requesting_handler):
        members_list = []
        for u_key in self.members:
            requesting_handler.log_read(generic.RegisteredUsers, "Getting an author from a Group's list of authors. ")
            member = u_key.get()
            if member:
                members_list.append(member)
            else:
                logging.warning("Group with key (%s) contains a broken reference to member (%s)"
                                % (self.key, u_key))
        return members_list

    def user_is_member(self, user):
        result = False
        for u_key in self.members:
            if user.key == u_key: result = True
        return result

    def add_member(self, requesting_handler, user):
        if user.key in self.members: return False
        self.members.append(user.key)
        requesting_handler.log_and_put(self, "Adding a new member. ")
        user.my_groups.append(self.key)
        requesting_handler.log_and_put(user, "Adding a new group to my_groups property")
        return True

    def list_updates(self, requesting_handler, user = None, n = UPDATES_TO_DISPLAY):
        assert type(n) == int
        assert n > 0
        requesting_handler.log_read(GroupUpdates, "Requesting %s updates. " % n)
        updates = GroupsUpdates.query(ancestor = self.key).order(-GroupUpdates.date).fetch(n)
        return updates

# Should have a Group as parent
class GroupUpdates(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add = True)
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    item = ndb.KeyProperty(required = True)

    def description_html(self, show_group_p = True):
        return generic.render_str("group_activity.html",
                                  author = self.author.get(),
                                  item = self.item,
                                  group = self.key.parent().get(),
                                  show_project_p = show_project_p)


######################
##   Web Handlers   ##
######################

class GroupPage(generic.GenericPage):
    def get_group(self, group_id, log_message = ''):
        self.log_read(Groups, log_message)
        return Groups.get_by_id(int(group_id))

    def put_and_report(self, item, author, group, other_to_update = None):
        self.log_and_put(item)
        # Log user activity
        u_activity = generic.UserActivities(parent = author.key, item = item.key, relative_to = project.key, actv_kind = "Groups")
        self.log_and_put(u_activity)
        # Log group update
        g_update = GroupUpdates(parent = group.key, author = author.key, item = item.key)
        self.log_and_put(g_update)
        self.log_and_put(group)
        if other_to_update: self.log_and_put(other_to_update)
        return


class NewGroupPage(generic.GenericPage):
    def get(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/new_group")
            return
        self.render("group_new.html")

    def post(self):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/new_group")
            return
        kw = {
            "g_name" : self.request.get("g_name"),
            "g_description" : self.request.get("g_description")}
        have_error = False
        if not kw["g_name"]:
            have_error = True
            kw["error"] = "Please provide a name."
            kw["name_class"] = "has-error"
        groups = Groups.query(Groups.name == kw["g_name"]).get()
        if groups:
            for g in groups:
                if user.key in g.members:
                    have_error = True
                    kw["error"] = "You are already in a group named " + kw["g_name"]
                    kw["name_class"] = "has-error"
        if have_error:
            self.render("group_new.html", **kw)
        else:
            group = Groups(name = kw["g_name"],
                           description = kw["g_description"],
                           members = [user.key])
            group.put()
            self.redirect("/g/%s" % group.key.integer_id())
            
                    
