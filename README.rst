==========
Gatekeeper
==========

Gatekeeper allows for "Set it and forget it!" behavior for your models.

There are two basic configurations:

1. You have a model where some number of instances of the model should be "live".   A good example of this would be an Article model, where you've written some articles that are "live", some that might've been taken down, some that are still "in progress", and others that are ready to "go live", but have a "go live" date that's in the future.

2. You have a model where ONE instance should be "live" depending on the underlying metadata of the model.   A good example of this would be a Homepage models:  you have different renditions of the home page that you want to go live at different date/times, but only one should be live at any given time.

Happily, we can accommodate both!

Other features:

1. If you're logged into the Django Admin, you can still "see" pages that aren't live (so you can easily QA things that are in progress).


Quick start
-----------

1. Add "gatekeeper" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'gatekeeper',
    ]


See the project README for more-detailed instructions of use.
