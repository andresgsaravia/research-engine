# Main file
# Basically it just loads everything

import webapp2
from src import *

app = webapp2.WSGIApplication([('/', frontend.MainPage),
                               # Users module
                               ('/login', users.LoginPage),
                               ('/logout', users.LogoutPage),
                               ('/signup', users.SignupPage),
                               ('/new_user', users.NewUserPage),
                               ('/settings', users.SettingsPage),
                               # Reviews module
                               ('/reviews', reviews.MainPage),
                               ('/reviews/new', reviews.New),
                               # Empty placeholders
                               ('/reviews/articles', frontend.UnderConstructionPage),
                               ('/reviews/blog_posts', frontend.UnderConstructionPage),
                               ('/news', frontend.UnderConstructionPage),
                               ('/notebook', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               ('/collaborations', frontend.UnderConstructionPage)],
                              debug = True)
