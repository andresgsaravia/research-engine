# frontend.py

import webapp2
import generic, projects, groups
import bibliography, code, collab_writing, datasets, forum, images, notebooks, wiki

class RootPage(generic.GenericPage):
    def get(self):
        user = self.get_login_user()
        projects = user.list_of_projects() if user else []
        p_updates = []
        if user:
            for p in projects:
                p_updates += p.list_updates(self, user)          # I query more items than needed... there should be a smart way to do this.
        p_updates.sort(key=lambda u: u.date, reverse = True)
        self.render("root.html", user = user, projects = projects, p_updates = p_updates[:30], show_project_p = True)


class UnderConstructionPage(generic.GenericPage):
    def get(self):
        self.render("under_construction.html")


class RemoveTrailingSlash(webapp2.RequestHandler):
    def get(self, url):
        self.redirect("/" + url)


class TermsOfServicePage(generic.GenericPage):
    def get(self):
        self.render("terms_of_service.html")


class OverviewPage(projects.ProjectPage):
    def get(self, projectid):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        updates = project.list_updates(self, user, projects.UPDATES_TO_DISPLAY)
        intro_p = (not updates) and user and user.list_of_projects() and (len(user.list_of_projects()) == 1)  # Display the intro if the project is new and its the only one.
        self.render("project_overview.html", project = project, 
                    overview_tab_class = "active",
                    authors = project.list_of_authors(self),
                    updates = updates,
                    intro_p = intro_p,
                    visitor_p = not (user and project.user_is_author(user)))
