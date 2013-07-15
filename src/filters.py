# Definitions for my own filters

import markdown, re, urllib


# Parsing doi (digital object identifier
# I will match a string of the form "doi:this/is.the/actual-doi" (Either doi, DOI or Doi will do)
# and transform it to [doi:doi:this/is.the/actual-doi](http://dx.doi.org/this/is.the/actual-doi"
# before passing it to markdown
DOI_REGEXP = r'(doi|Doi|DOI):\S+'

def make_doi_link(doi_match_object):
    s = doi_match_object.group(0)
    return "[%s](http://dx.doi.org/%s)" % (s, urllib.quote(s[4:]))

def md(value):
    value = re.sub(DOI_REGEXP, make_doi_link, value)     # doi links
    return markdown.markdown(value, extensions = ['extra', 'toc', 'nl2br', 'mathjax', 'tables'])
