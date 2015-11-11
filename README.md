Research Engine
===============

> *I believe that the process of science - how discoveries are made - will change more in the next twenty years than it has in the past 300 years.* Michael Nielsen. *Reinventing Discovery* (2012).

> *Rather, knowledge is becoming inextricable from - literally unthinkable without - the network that enables it. Our task is to learn how to build smart rooms - that is, how to build networks that make us smarter, especially since, when done badly, networks can make us distressingly stupider.* David Weinberger. *Too Big To Know* (2012).


My vision
---------

I'm a guy trying to be a successful scientist and I'm convinced it's time to change the way we do Science. And I'm also convinced that the way to change it is using the most powerful cognitive tool we have now: the Internet. I believe David Weinberger's quote above to be absolutely right, we have now the means of providing humanity an [extended mind][xkcd extended mind] for the benefit of all. But we, scientists, are too reluctant to make the jump, while we probe the limits of human mind's capabilites every day (well, at least we try) we haven't changed the way we do science in hundreds of years.

Right now, the minimun contribution to science (for which you can get credit for) is a *journal article*. And this is no easy feat to achieve. Usually a published article represents the culmination of many months of work, after spending months browsing the literature, making many trials and erros and following dead-ends, when you finally find something worthy, you write a distilled pristine text with your shining result and send it to publication. I'm not arguing ([for now][misquoting Churchill]) against the value of journal articles. What I'm concerned is that a journal article is the *minimum and only* way to make a contribution to science that will get a scientist some reward for his/her work. All the errors, dead-ends and partial results get lost to the overall community. And I'm convinced all that unpublished information is not only valuable but should be rewarded.

Take as a contrasting example the *open source* community. I don't think we can easily overstate the impact open source software has had in the world. But take a look at [this study][one-line], the authors find that *the most common size of code contribution is one line of source code*. Imagine if it was forbidden to make such a meager contribution to an open source project, imagine you needed to change at least 200 lines of code to be considered for a contribution, imagine also that your contribution had to go through a *peer-review* process which can take from a couple of weeks, to many months (my last experience was 8 months long). And God help you if you copy-pasted a line from some place else! Certainly you wouldn't bother to correct a typo or make a micro-optimization when you had the chance. That's why I'm frustrated when I see a clear error or a possible improvement in a published article, I wish I could share and discuss my small contribution to everyone else reading that article, but it's really hard to do that. In general it's really hard to contribute to and/or correct the scientific record in any way.

And don't get me started on the [exhorbitant high prices and abusive policies from publishers][The Cost of Knowledge]!

If you think about it, science is perhaps humanity's most impressive collaboration. It spans many centuries of cumulative work from people all around the world. It's thus equally impressive that our tools for collaborative work haven't been improved. I think the only significant change has been from traditional mail to e-mail. But it's clear now that there are many successful ways to collaborate in large scale. Take also a look at [this post from Aaron Swartz][Who writes Wikipedia] about how [Wikipedia][] is written. The most common contributions, as in the open source movement, are also simple changes, mostly of spelling and formatting. But most of the information comes from a wide range of casual contributors who happened to be experts in a small (sub)topic. The editors with most contributions mostly provide coherence and structure to the whole site. Perhaps we can learn a lesson here and try to incorporate the general public in our intellectual endeavour. Already we have some [citizen science][] with amazing results.

I think we need to restructure the way we work with scientific knowledge. First we need to acknowledge that all intellectual production is potentially valuable including dead-ends, negative results and even personal opinions so we should record it all in some way that makes it accesible to everyone who could use it. We also neeed to encourage small contributions, more dynamic discussions and better collaborations. Then we need to find some way to give credit where credit is due. This is still very far away from my dream of an humanity's *extended mind* to the benefit of everyone but perhaps this will start to light the way. None of the ideas I previoulsy stated are new, and I'm glad to see a growing comunity of scientists concerned with new ways of working. 


My motivation
-------------

My aim in building [Research Engine][] can be stated as:

> Every intellectual activity related to my research is valuable and should be recorded in an open, organized and accesible way that can be escalated to bigger collaborations.

By *intellectual activity* I mean many things including my notes while working through a problem, my thoughts and critics while reading someone else's work, the source code I use for my projects and also smaller one-time-use snippets, the datasets I get from experiments and/or simulations, the discussions I have with colleagues and finally the cumulative knowledge I gain through time in a topic.

There are some projects where I could keep a record of many of these things. For example I like [Academia.edu][] where you can share *Facebook-style* thoughts about your research and find colleagues with similar interests. I think also [ResearchGate][] has the right idea by promoting discussion and trying to measure the impact of your contributions in a more widely sense than just publications. Another interesting site is [figshare][] where you can post some of your partial or negative results. For some time I also used a [WordPress][] blog as [my open science notebook][]. However, after some time, I found that none of these sites provided just what I wanted and they aren't integrated in any way. However, my main motivation is that all of them put emphasis in *sharing* but not much thought in providing better ways to *create* new knowledge in innovative ways.


My intended contribution
------------------------

As I said before, I split the idea of *intellectual activity* in a couple of different things, in particular I broke it down to six different concepts and I'm implementing each one of those variants as a separated section in Research Engine. Here I to outline how I treat them:

- **Notebook**: The first thing I do when working through a problem is keeping a time-ordered record of my progress. By that, I mean that I use a notebook to keep track of the different things I do. It's important that this knowledge is progressive, that is, improves with time and generally the last note has my latest insight. I also have many notebooks for a single project with each one focusing on different aspects or approaches. I find that a blog-like platform is quite adequate so in Research-Engine I treat each notebook as a separete blog. I also think that interesting discussions arise from particular details in some notes so, while a notebook is *private* in the sense that only the owner can write to it, I have a comment section for each note to promote discussion of ideas.
- **Wiki**: After working in a topic from some time you start to consolidate some knowledge that's unfit to keep in a notebook. You start to gain a cumulative and deeply interconnected knowledge that starts to be too big for your head so you want to lay it down somewhere where you can come back to it when you need it. It's a record of the results and key
concepts related to your interests but not a description of your journey through them. You could try (and I did try) to write some *summary notes* in your notebook and make hyperlinks from one to the other but it gets clumsy and ineficient very soon. I think an *encyclopedic-style* is better suited and Wikipedia has the best example of it. So I made this section into a Wiki. This section is *public* in the sense that all the members of a project should be able to contribute to it.
- **Writings**: If you are a scientist surely you want to publish articles in a journal or in another kind of publication. For this kind of intellectual activity you may want to have some sort of version control and collaborative writing capabilites. Usually the process involves one author acting as coordinator sending different versions of the writing to everyone and trying to get them to work in syncrony making corrections and agreeing on which is the *current* version of the article they're supposed to be working on. It works relatively fine if the number of collaborators is small but it escalates badly. I think a better way to to this is to treat each collaborative writing similar to a single Wiki page but with a space to keep track not only of the content of the writing but also of it's status (such as, *waiting for the referees*, *needs correction*, *published in...*, etc.)
- **Code**: It's everyday more common that you will need to write some source code for a part of your project. If it's a very complex simulation algorithm surely you want to have a fully-fledged version control system with many people discussing and collaborating but if it's a small snippet you may also want to have some record of it in case you (or someone else) need it in the future for a similar use. Besides, sometimes it's different how a program *works* than how you are *using it*. In this section I want to have links and discussions about any kind of source code used for the current project. 
- **Dataests**: If you are an experimental scientist or if you make simulations you will come across many datasets and surely you want to keep them secure, ordered and with all their appropiate metadata. Also you may repeat experiments and/or calculations with better techniques so you may also want to have some kind of *version-control* for each dataset. That's what I try to implement here. I think of a *dataset* as all the data gathered from a single experiment or simulation run. But each experiment or simulation may throw a lot of different data, for example, if you measure three different properties of a material as a function of time you will end with three different tables. I call each one of those a *data concept* (for lack of a better term) and each of those *concepts* can have many *revisions*.
- **Forum**: This is pretty straightforward, I just want a place to engage in lively discussions around any issue related to the project. Of course, it's also important to keep a record of there conversations.

This project is based on [Google's App Engine][] so it should be relatively easy to escalate and improve. I assume most of the improvements will be made by researchers so they need to be able to make changes easily and return to their science production as fast as possible.


To do
=====

You can have a look at the features I'm planing to implement and the bugs I've found in the [issues tab][] of this GitHub repository. Besides those ideas I also want to do the following:

- **Find money**: To be able to escalate this project to many users.
- **Raise awareness**: Of the need to change the way we make science.
- **Get feedback**: From my colleagues in how to improve our endeavours.
- **Improve the site**: By getting professional programmers (not amateurs like me) and some graphic designers so this place looks and feels really professional.
- **Provide the world with ubiquitous WiFi**: Or, maybe, find some way to be able to work on Research Engine wihtout having an active Internet conection.


Hacking
=======

If you want to play around with the code you will need [Google's App Engine][], please look into their documentation for instructions on how to get an instance working on your machine. If you want to make it public you will also need to register an app with them and change some basic settings:

- In the `app.yaml` file change the line `application: research-engine` to your own app name.
- In the `mail.py` file change the `ADMIN_EMAIL = "admin@research-engine.appspotmail.com"` parameter to your own appspot domain.
- In the `src/generic.py` file change the parameters `APP_URL`, `ADMIN_EMAIL` and `APP_REPO`. Be sure that you use `ADMIN_EMAIL` consistently.
- Optionally you may want to change the few instances in which *Research Engine* and its url are mentioned in the `static/edit_help.html` file
.
- Copy the `src/secrets.py.template` to `src/secrets.py` and fill in the appropriate information to your app. In the current version of this app we only use Google Login so you can leave the other options without modification. To use the *Log in with Google* feature you will need to register a new App in your [Google Cloud console][] for your appspot domain and copy its OAuth 2.0 CLIENT ID and CLIENT SECRET keys in this file. In the OAUth 2 options add as *web origins* `https://your-app-name.appspot.com` and `http://localhost:8080` and as *redirect uris* `https://your-app-name.appspot.com/auth/google/callback` and `http://localhost:8080/auth/google/callback`.
- You will need yo register the `ADMIN_EMAIL` parameter you wrote on `src/generic.py` in CrossRef. To do this you should go to <http://www.crossref.org/requestaccount/> and submit there your `ADMIN_EMAIL`. They will send you a verification link which you can check in your app's logs.


License
=======

Code developed here is released under a [GNU GPLv3][] license so you have the freedom to do a lot of things with it, but please look into it's details before using this package. You can find a copy of it in `doc/LICENSE.txt` file or in [this GPLv3 page][GNU GPLv3]

[misquoting Churchill]: http://cameronneylon.net/blog/what-is-it-with-researchers-and-peer-review-or-why-misquoting-churchill-does-not-an-argument-make/?utm_source=feedly&utm_medium=feed&utm_campaign=Feed%3A+ScienceInTheOpen+%28Science+in+the+open%29
[GNU GPLv3]: http://www.gnu.org/licenses/gpl-3.0.html
[Google's App Engine]: https://developers.google.com/appengine
[Wikipedia]: https://www.wikipedia.org
[xkcd extended mind]: https://www.xkcd.com/903/
[one-line]: http://dirkriehle.com/2008/09/23/the-dominance-of-small-code-contributions/
[Who writes Wikipedia]: http://www.aaronsw.com/weblog/whowriteswikipedia
[issues tab]: https://github.com/andresgsaravia/research-engine/issues?state=open
[The Cost of Knowledge]: http://thecostofknowledge.com/
[citizen science]: https://en.wikipedia.org/wiki/Citizen_science
[Academia.edu]: http://academia.edu/
[ResearchGate]: http://www.researchgate.net/
[FigShare]: http://figshare.com/
[WordPress]: https://wordpress.org/
[my open science notebook]: http://notebook.andresgsaravia.com.mx/
[Research Engine]: https://research-engine.appspot.com/
[Google Cloud console]: https://cloud.google.com/console
