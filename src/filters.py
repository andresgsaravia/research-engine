# Definitions for my own filters

import markdown

def md(value):
    return markdown.markdown(value, extensions = ['extra', 'toc', 'nl2br', 'mathjax'])
