# groups.py
# For creating, managing and updating groups.

from datetime import datetime, timedelta
from google.appengine.ext import ndb
import generic, email_messages, projects
import bibliography   # I should move stuff from bibliography to a more generic module

UPDATES_TO_DISPLAY = 30           # number of updates to display in the Overview tab
DATETIME_STR = "%d.%m.%Y %H:%M"   # For converting to and from python's datetime and datetimepicker.js

###########################
##   Datastore Objects   ##
###########################

class Groups(ndb.Model):
    name         = ndb.StringProperty(required = True)
    description  = ndb.TextProperty(required = False)
    members      = ndb.KeyProperty(repeated = True)
    started      = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

    def list_members(self):
        members_list = []
        for u_key in self.members:
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

    def list_updates(self, requesting_handler, n = UPDATES_TO_DISPLAY):
        assert type(n) == int
        assert n > 0
        requesting_handler.log_read(GroupUpdates, "Requesting %s updates. " % n)
        updates = GroupUpdates.query(ancestor = self.key).order(-GroupUpdates.date).fetch(n)
        return updates

    def new_update(self, item):
        new_update = GroupUpdates(author = item.author,
                                  item   = item.key,
                                  parent = self.key)
        new_update.put()
        self.put()


# Should have a Group as parent
class GroupUpdates(ndb.Model):
    date   = ndb.DateTimeProperty(auto_now_add = True)
    author = ndb.KeyProperty(kind = generic.RegisteredUsers, required = True)
    item   = ndb.KeyProperty(required = True)

    def description_html(self, show_group_p = True):
        return generic.render_str("group_activity.html",
                                  author = self.author.get(),
                                  item = self.item,
                                  group = self.key.parent().get())

# Should have a Group as parent
class CalendarEvents(ndb.Model):
    start_date  = ndb.DateTimeProperty(required = True)     # Maybe later I'll add an "end_date"
    added       = ndb.DateTimeProperty(auto_now_add = True)
    author      = ndb.KeyProperty(required = True)
    description = ndb.TextProperty(required = False)

    def send_email_notifications(self, update = False, edit_author = False):
        group   = self.key.parent().get()
        members = group.list_members()
        author  = self.author.get() if (not edit_author) else edit_author
        for member in members:
            email_messages.send_new_calendar_event_notification(user = member, author = author,
                                                                group = group, event = self,
                                                                update = update)
            

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
        groups = Groups.query(Groups.name == kw["g_name"]).fetch()
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
            user.my_groups.append(group.key)
            user.put()
            self.redirect("/g/%s" % group.key.integer_id())

class ViewGroupPage(GroupPage):
    def render(self, *a, **kw):
        GroupPage.render(self, overview_tab_class = "active", *a, **kw)

    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        self.render("group_overview.html", group = group, user = user,
                    members = group.list_members(),
                    updates = group.list_updates(self))


class CalendarPage(GroupPage):
    def render(self, *a, **kw):
        GroupPage.render(self, calendar_tab_class = "active", *a, **kw)

    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        display_date = datetime.today() - timedelta(days=1)
        events = CalendarEvents.query(ancestor = group.key).filter(CalendarEvents.start_date > display_date).order(CalendarEvents.start_date).fetch()
        self.render("group_calendar.html", group = group, user = user, events = events)


class CalendarNewTask(CalendarPage):
    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        self.render("group_calendar_event.html", group = group, user = user,
                    title = "Add new event", btn_text = "Create event")

    def post(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        kw = {"date"        : self.request.get("date"),
              "description" : self.request.get("description"),
              "title"       : "Add new event",
              "btn_text"    : "Create event"}
        have_error = False
        if not kw["date"] :
            have_error = True
            kw["error_message"] = "Please select a date for the event."
            kw["date_class"] = "has-error"
        elif not kw["description"]:
            have_error = True
            kw["error_message"] = "Please provide a description for the event."
            kw["description_class"] = "has-error"
        if have_error:
            self.render("group_calendar_event.html", group = group, user = user, **kw)
        else:
            new_event = CalendarEvents(start_date = datetime.strptime(kw["date"], DATETIME_STR),
                                       author = user.key,
                                       description = kw["description"],
                                       parent = group.key)
            new_event.put()
            group.new_update(new_event)
            new_event.send_email_notifications()
            self.redirect("/g/%s/calendar" % groupid)


class EditEvent(CalendarPage):
    def get(self, groupid, eventid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        event = CalendarEvents.get_by_id(int(eventid), parent = group.key)
        if not event:
            self.render("404.html", info = "Event %s not found." % eventid)
        self.render("group_calendar_event.html", group = group, user = user,
                    title = "Edit event", btn_text = "Save changes", notify_checkbox = True,
                    date = datetime.strftime(event.start_date, DATETIME_STR),
                    description = event.description)


    def post(self, groupid, eventid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        event = CalendarEvents.get_by_id(int(eventid), parent = group.key)
        if not event:
            self.render("404.html", info = "Event %s not found." % eventid)
        kw = {"date"            : self.request.get("date"),
              "description"     : self.request.get("description"),
              "title"           : "Edit event",
              "btn_text"        : "Save changes",
              "notify_checkbox" : self.request.get("notify") == "on"}
        have_error = False
        if not kw["date"] :
            have_error = True
            kw["error_message"] = "Please select a date for the event."
            kw["date_class"] = "has-error"
        elif not kw["description"]:
            have_error = True
            kw["error_message"] = "Please provide a description for the event."
            kw["description_class"] = "has-error"
        if have_error:
            self.render("group_calendar_event.html", group = group, user = user, **kw)
        else:
            event.start_date = datetime.strptime(kw["date"], DATETIME_STR)
            event.description = kw["description"]
            event.put()
            if kw["notify_checkbox"]:
                event.send_email_notifications(update = True, edit_author = user)
            self.redirect("/g/%s/calendar" % groupid)


class AdminPage(GroupPage):
    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        self.render("group_admin.html", group = group, user = user, members = group.list_members())
 
    def post(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group or not group.user_is_member(user):
            self.render("404.html", info = "Group %s not found or you are not a member of this group." % groupid)
            return
        kw = {"action" :self.request.get("action")}
        if kw["action"] == "invite":
            kw["username"] = self.request.get("username")
            invited_user = self.get_user_by_username(kw["username"].lower())
            if not invited_user:
                kw["error_message"] = "No username <em>%s</em> found" % kw["username"]
            elif not group.user_is_member(user):
                kw["error_message"] = "You are not a member of this group"
            elif invited_user.key in group.members:
                kw["error_message"] = "%s is already a member of %s" % (invited_user.username.capitalize(), group.name)
            else:
                email_messages.send_invitation_to_group(group = group,
                                                        inviting = user,
                                                        invited = invited_user)
                kw["message"] = "Invitation sent to <em>%s</em>" % invited_user.username.capitalize()
        else:
            kw["error_message"] = "Something went wring while processing your request."
        self.render("group_admin.html", group = group, user = user, members = group.list_members(), **kw)


class InvitedPage(GroupPage):
    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s" % groupid)
            return
        group = self.get_group(groupid)
        if not group:
            self.render("404.html", info = "Group %s not found." % groupid)
            return
        h = self.request.get("h")
        if h and (generic.hash_str(user.salt + str(group.key)) == h) and not group.user_is_member(user):
            group.add_member(self, user)
        self.redirect("/g/%s" % groupid)


class BiblioPage(GroupPage):
    def render(self, *a, **kw):
        GroupPage.render(self, bibliography_tab_class = "active", *a, **kw)

    def get(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s/bibliography" % groupid)
            return
        group = self.get_group(groupid)
        if not group:
            self.render("404.html", info = "Group %s not found." % groupid)
            return
        bibitems = bibliography.BiblioItems.query(ancestor = group.key).order(-bibliography.BiblioItems.last_updated).fetch()
        self.render("group_biblio.html", user = user, group = group, bibitems = bibitems)

    def post(self, groupid):
        user = self.get_login_user()
        if not user:
            self.redirect("/login?goback=/g/%s/bibliography" % groupid)
            return
        group = self.get_group(groupid)
        if not group:
            self.render("404.html", info = "Group %s not found." % groupid)
            return
        have_error = False
        kw = {"identifier" : self.request.get("identifier").strip(),
              "kind" : self.request.get("kind")}
        if not kw["identifier"]:
            have_error = True
            kw["error_message"] = "Please write an appropiate value on the seach field. "
            kw["identifier_class"] = "has-error"
        else:
            # Check if already present
            bibitem = bibliography.BiblioItems.query(bibliography.BiblioItems.kind == kw["kind"],
                                        bibliography.BiblioItems.identifier == kw["identifier"],
                                        ancestor = group.key).get()
            if not bibitem:
                item_dom, kw["error_message"] = bibliography.get_dom(kw["identifier"], kw["kind"])
                if kw["error_message"]: 
                    have_error = True
                else:
                    metadata = bibliography.parse_xml(item_dom, kw["kind"])
                    bibitem = bibliography.BiblioItems(title = metadata["title"],
                                                       link = bibliography.make_link(kw["identifier"], kw["kind"]),
                                                       kind = kw["kind"],
                                                       identifier = kw["identifier"],
                                                       metadata = metadata,
                                                       parent = group.key)
        # Add to the library
        if have_error:
            kw["bibitems"] = bibliography.BiblioItems.query(ancestor = group.key).order(-bibliography.BiblioItems.last_updated).fetch()
            self.render("group_biblio.html", user = user, group = group, **kw)
        else:
            bibitem.put()
            self.redirect("/g/%s/bibliography" % groupid)


class SendBiblioNotifications(GroupPage):
    def get(self):
        all_groups = Groups.query()
        for group in all_groups:
            one_week_ago = datetime.today() - timedelta(days=7)
            bibitems = bibliography.BiblioItems.query(ancestor = group.key)
            bibitems.filter(bibliography.BiblioItems.last_updated > one_week_ago).order(-bibliography.BiblioItems.last_updated).fetch()
            if bibitems:
                for user in group.members:
                    email_messages.send_group_biblio_notification(group = group, user = user.get(), bibitems = bibitems)
                
