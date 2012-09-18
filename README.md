Research Engine
===============

This project aims to bring together some of the most useful tools in a researcher's daily work. It is intended to be a place to facilitate the organization of knowledge, ideas and resources needed to do research. This project also stems from the spirit of [Open Science](https://en.wikipedia.org/wiki/Open_science) trying to make non-sensitive content freely accessible to anyone thus facilitating and potentiating research capabilities.

The framework used is [Google's App Engine](https://developers.google.com/appengine/) with Python 2.7. You can access this application on it's [Appspot website](http://research-engine.appspot.com/) however it's not anywhere near to provide even basic functionality at this time. 

I will provide some documentation and status updates in the doc/ folder.

## Motivation ##

> *I believe that the process of science - how discoveries are made - will change more in the next twenty years than it has in the past 300 years.* Michael Nielsen. *Reinventing Discovery* (2012).

> *Rather, knowledge is becoming inextricable from - literally unthinkable without - the network that enables it. Our task is to learn how to build smart rooms - that is, how to build networks that make us smarter, especially since, when done badly, networks can make us distressingly stupider.* David Weinberger. *Too Big To Know* (2012).

Online tools are becoming essential in modern research, however there isn't any integrated services. I find myself hopping around between my email, calendar, RSS reader, [Mendeley](http://www.mendeley.com/), [Wordpress](http://wordpress.org/) blog, [MediaWiki](http://www.mediawiki.org/) site and several other services during a typical day and I am still lacking some tools to improve my teaching and collaborate with colleagues in many respects.

It is my intention to bridge that gap as best as I can. I am not a *professional* programmer but I hope to make a concept-design good enough to gain some collaboration later on.


## Overview ##

As I envision, the work of a researcher fall into three closely related categories:
- **Learning:** This includes general references like textbooks or [Wikipedia](http://www.wikipedia.org) but also specialized resources like journal articles, conferences, webinars and online courses.
- **Teaching:** Researchers are often required to provide lectures to new students but there are many other *teaching* activities like writing divulgation articles for a general public, maintaining a repository of specialized knowledge or giving a talk in a conference. I would also include here giving an opinion about other people's articles.
- **Production:** The actual *meat* of research is producing new knowledge and advancing the scientific understanding. This often (but not always) involves writing articles and submitting them to journals. I think we particularly lack tools to work un collaboration. 

### Learning ###

The main source of learning for a scientist is journal articles. I would like to have simple and systematic way of organizing the literature according to interest areas and in a sequential way. It would also be nice to have some sort of tracking according to citations to give a clear panorama of the development of concepts. It is also crucial to have a way to make highlights and notes and be able to share them with colleagues. Much of this functionality is provided by [Mendeley](http://www.mendeley.com/) so perhaps using their API is appropiate, however their services are limited for a free account and I consider their proces rather steep.

To keep up with the latest news there should be a way to aggregate RSS feeds (perhaps even use a ppppcurrent Google Reader account) and easily translate one such entry to an article entry. Perhaps some social capabilities like Twitter, Facebook or Google+ would be nice but I will procastrinate on this one since I'm not sure it would be a good idea. 

Another important aspect is to have a way to be informed about upcoming conferences, seminars, webinars, Google+ hangouts or online courses. Perhaps an integration with Google Calendar (or other calendar services) would be helpful also.

### Teaching ###

The world is changing the way it learns specialized topics. I really like projects like [Udacity](http://udacity.com) and [Coursera](http://coursera.org). There are terrific toold for online teaching like [Moodle](http://moodle.org) but, since I'm using Google's App Engine I think it's worth exploring the newly born [Course Builder](https://code.google.com/p/course-builder).

### Production ###

I consider as *production* many things. Of course we need to write journal articles since the infamous *publish or perish* is still the norm. But we also produce much more content than that which could be improved and shared with the help of online tools. For example blog entries for the lay audience and for specialized readers, review of articles, comments about recent news, seminar talks, software coding.

An integration with version control platforms (such as [GitHub](https://github.com) or [Launchpad](https://launchpad.net) could be useful for software writing (however it may be unnecesary) and [Google Drive](https://drive.google.com) or [Dropbox](https://www.dropbox.com) could be nice for the collaborative writing of papers.

## Installation ##

If you want to play around with the code you will need [Google's App Engine](https://developers.google.com/appengine/), please look into their documentation for instructions on how to get an instance working on your machine. If you want to make it public you will also need to register an app with them.

## License ##

Code developed here is released under a [GNU GPLv3](http://www.gnu.org/licenses/gpl-3.0.html) license so you have the freedom to do almost anything you like with it, but please look into it's details before using this package. You can find a copy of it in doc/LICENSE.txt or in [this link](http://www.gnu.org/licenses/gpl-3.0.html)
