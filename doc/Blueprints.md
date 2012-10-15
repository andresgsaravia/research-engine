Blueprints
==========

Here you can find a brief description of how Research Engine is structured.


## Files ## 

> /research-engine:
>
> README.md
> app.yaml               Handlers definitions for files and scripts.
> css/                   Stylesheets.
> doc/                   Documentation.
> home.py                Url mapping.
> images/                Relevant to the site (not user-specific).
> src/                   All the Python source code.
> templates/             HTML Jinja2 templates.

I try to make the code in very modular and as independent as possible. Each source file inside the src/ folder has a particular use.

> /research-engine/src:
>
> __init__.py            Module listing.
> frontend.py            Main and some auxiliary pages.
> generic.py             Basic functionality. All modules inherit this one.
> library.py             Knowledge database and user's library.
> tests.py               To make sure everything is working.
> users.py               Login, signup and the sort.


## Data models ##

### Knowledge databases (library.py) ###

WARNING: All the following information is work in progress even though it is written as if it already exists. I'm still learning Datastore's functionalities so my ideas may be completely wrong.

I think of published articles, arXiv preprints, blog posts, code snippets or projects as having the same hierarchy. Each one of them represents one "knowledge item" and is stored in the KnowledgeItems database which is user-independent. This database is updated (if necessary) each time a user adds a new item to their personal library. 

There is a database for each kind of knowledge item (arXiv, published article, etc...) and each element has as parent an element of KnowledgeItems.

Every user's review of a KnowledgeItem is a child of that particular item. For example, a Review of an arXiv preprint has as parent an element of the arXiv database which in turn has as parent an element of KnowledgeItems. 

Each user has a personal library with their personal Reviews of KnowledgeItems. Since Reviews are (grand)childs of KnowledgeItems its elements are only references to those reviews. A review can be empty if the user just wants to track that element but doesn't want to comment on it.


### Users (users.py) ###

(needs update)
