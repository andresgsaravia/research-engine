# Definitions for my own filters

import markdown, re, urllib, bleach


# Parsing doi (digital object identifier
# I will match a string of the form "doi:this/is.the/actual-doi" (Either doi, DOI or Doi will do)
# and transform it to [doi:this/is.the/actual-doi](http://dx.doi.org/this/is.the/actual-doi"
# before passing it to markdown
DOI_REGEXP = r'(doi|Doi|DOI):\S+'

def make_doi_link(doi_match_object):
    s = doi_match_object.group(0)
    return "[%s](http://dx.doi.org/%s)" % (s, urllib.quote(s[4:]))


# This regexp finds MediaWiki-like inner links in the following way.
# A simple [[link and text]]                 -->   (''       , 'link and text')
# Another [[link | display text]]   -->   ('link |' , 'display text') 
WIKILINKS_RE = r'\[\[([^\|\]]+\|)?([^\]]+)\]\]'

# Given a link prefix and assuming the regex r'\[\[([^\|\]]+\|)?([^\]]+)\]\]'
# was used, this function returns the link and display text to be used un an
# html <a ...> tag.
def link_and_text(mobject, link_prefix):
    text = mobject.groups()[1].strip()
    if mobject.groups()[0]:
        link_posfix = mobject.groups()[0][:-1].strip().replace(" ","_")
    else:
        link_posfix = text.replace(" ", "_")
    link_posfix = link_posfix[:1].upper() + link_posfix[1:]
    return (link_prefix + link_posfix, text)

# Returns a function suitable to use inside a re.sub(...) call to generate
# a valid htlm <a ...> tag inside a wiki.
def make_sub_repl(projectid):
    link_prefix = "/%s/wiki/page/" % projectid
    return lambda x: '<a href="%s">%s</a>' % (link_and_text(x, link_prefix))


def md(value, wiki_p_id = ""):
    "wiki_p_id is the project id and should only be present when rendering a wiki page. This is used to generate the 'wikilinks'."
    allowed_tags = bleach.ALLOWED_TAGS + ['br', 'caption', 'colgroup', 'div', 'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
                                          'iframe', 'img', 'mathjax', 'p', 'pre', 'span', 'sub', 'sup','table', 'tbody', 'tfoot',
                                          'td', 'th', 'thead', 'tr']
    allowed_attrs = dict(bleach.ALLOWED_ATTRIBUTES.items() + 
                         {'*' : ['class', 'id', 'align', 'style'],
                          'img': ['alt', 'src', 'title', 'width', 'height'],
                          'iframe' : ['width', 'height', 'src', 'frameborder', 'allowfullscreen']}.items())
    value = re.sub(DOI_REGEXP, make_doi_link, value)     # doi links
    if wiki_p_id: value = re.sub(WIKILINKS_RE, make_sub_repl(wiki_p_id), value) 
    value = markdown.markdown(value, extensions = ['extra', 'toc(title=Contents)', 'nl2br', 'mathjax', 'tables', 'codehilite'])
    value = bleach.clean(value, tags = allowed_tags, attributes = allowed_attrs)
    return value
