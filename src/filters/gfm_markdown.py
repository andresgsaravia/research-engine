# Source taken from http://www.mayinhosa.com/post/1/markdown-in-google-appengine

import markdown, gfm

def gfm_markdown(value):
    "Processes markdown and Git Hub Flavoured Markdown on the string."
    return markdown.markdown(gfm.gfm(value))
