# Definitions for my own filters

import markdown

def wikify(value):
    return markdown.markdown(value, extensions = ['extra', 'toc', 'nl2br', 'mathjax','wikilinks'])

def md(value):
    return markdown.markdown(value, extensions = ['extra', 'toc', 'nl2br', 'mathjax'])
