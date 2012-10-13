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
                               ('/library', library.MainPage),
                               ('/library/articles', library.Articles),
                               ('/library/blog_posts', library.BlogPosts),
                               ('/library/software', library.Software),
                               ('/library/new', library.New),
                               # Empty placeholders
                               ('/reviews/articles', frontend.UnderConstructionPage),
                               ('/reviews/blog_posts', frontend.UnderConstructionPage),
                               ('/news', frontend.UnderConstructionPage),
                               ('/notebook', frontend.UnderConstructionPage),
                               ('/classroom', frontend.UnderConstructionPage),
                               ('/collaborations', frontend.UnderConstructionPage),
                               # Tests
                               ("/tests/big_page", tests.BigPage)],
                              debug = True)
