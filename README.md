# Gatekeeper

Gatekeeper is a simple Django app that enables "Set it and Forget it!" publishing behavior for models.



## Quick start

1. Add "gatekeeper" to your INSTALLED_APPS setting like this::

    ```
    INSTALLED_APPS = [
        ...
        'gatekeeper',
    ]
    ```

# Gatekeeping Models

The main use for gatekeeping is where you have a model with many instances, but you only want some to be "live" on the site.

A good example is a generic "Article" model:

    * Some articles are ready-to-go and you want them live to the public;
    * Other articles are still being worked on - you want to be able to preview them, but not take them live JUST yet;
    * Some articles might be pulled (and re-published later)
    * Some articles are ready to be published, but you want them to only go live at a later date.
    
Here, all you need to do is subclass the `GatekeeperAbstractModel` abstract class, e.g.:

```
from django.db import models
from gatekeeper.models import GatekeeperAbstractModel

class Article(GatekeeperAbstractModel):
    ... (your custom fields go here)
```

The superclass creates two fields:

1. `live_as_of` (DateTime, default = None) - this is the timestamp of when the object should go live.  If it's not set (None) you can think of this as an "in development" phase.  For an Article model, you've created the instance, but you're still writing the Article.  You can preview it through the Admin, but it's not live on the site.

2. `publish_status` (controlled vocabulary, default = None) - this has 4 possible values:

    * None = has never been published
    * 0 = "use live_as_of" date to determine if the object is available to the public
    * 1 = "always on" - hard-wired to be always available to the public
    * -1 = "permanently off" - hard-wired to NEVER be available to the public

You set the `publish_status` and `live_as_of` values through the Admin.

## View Code

Setting up gatekeeping for models is easy!  Using the Article model as an example, here is the corresponding view code for a listing and a detail view.

```
from django.views.generic import DetailView, ListView
from .models import Article
from gatekeeper.mixins import GatekeeperListMixin, GatekeeperDetailMixin

class ArticleListView(GatekeeperListMixin, ListView):
    model = Article
    template_name = 'article/article_list.html'
    context_object_name = 'articles'
    
        
class ArticleDetailView(GatekeeperDetailMixin, DetailView):
    model = Article
    template_name = 'article/article_detail.html'
    context_object_name = 'article'
```

What's happening behind the scenes:

1. In the ListView, the gatekeeper is filtering the model with the following rules:

    1. If the user is logged into the Admin and `publish_status` != -1, _include the model instance_
    2. If there is no user, and the `publish_status` = 1, _include the model instance_
    3. If there is no user, `publish_status` = 0, *and* the current date/time > `live_as_of`, _include the model instance_.
    4. Return the filtered list of model instances.
    
2. In the DetailView, the gatekeeper follows the same rules, but will throw a 404 error, if the user is not logged into the Admin and the request object isn't "live" yet.

## Using the Gatekeeper with querysets in your own code

Say there's a section on your homepage that gives a list of the three most recent articles.  If you just create a queryset along the lines of:

```most_recent_articles = Article.objects.order_by(-date_created)[:3]```

it will include articles regardless of what their gatekeeping situation is.

So there are two helper functions to apply the gatekeeping rules to any queryset you generate.

### `view_gatekeeper`

This takes a queryset, applies the rules and returns a filtered queryset.

```
from gatekeeper.view_utils import view_gatekeeper
...
recent_articles = Article.objects.order_by('-date_created')
recent_articles = view_gatekeeper(recent_articles, is_auth)
...
```

The `is_auth` parameter allows you to filter based on whether the user making the request is logged in or not.  If they are logged in, then objects that aren't live but still available to the Admin will "pass" through the gatekeeper.   For this, you'd set `is_auth = self.request.user.is_authenticated`.   (About the only time I can see doing this is if you want to see how a particular non-live object will "play" in a generated content feature.)

I've found that I almost NEVER need that.  Typically for constructed lists of object you want to only see what IS live, so in almost every case where I've used `view_gatekeeper`, I've set `is_auth = False`.   You can still "see" all the non-live objects through their detail page when you're logged into the Admin. 

### `object_gatekeeper`

This takes a single object instance and returns True or False depending on whether it "passes" the gate.

```
from gatekeeper.view_utils import object_gatekeeper
...
my_article = Article.objects.first()
am_i_avaiable = object_gatekeeper(my_article, is_auth)
...
```

Generally, you don't need this method since the model property `available_to_public` already exists.   The one case where I've needed it was when I had a list come from an outside source where there was an overlap with objects in one of my models.   I wanted to show all the external object, and construct links to the object that overlapped but ONLY if they were live.

# Gatekeeping Model Instances Serially

In some situations, you only want a single instance of model to be "live" on the site at a time.   You can use the Gatekeeper to do this.   

A good example would be a Home page app.   You can queue up different renditions of the home page to go live at different times.

Here, there's only a small change to the model and view code:

```
from django.db import models
from django.utils.translation import ugettext_lazy as _
from gatekeeper.models import GatekeeperSerialAbstractModel

class Homepage(GatekeeperSerialAbstractModel):
    title = models.CharField (
        _('Title'),
        max_length = 200,
        null = False
    )

    def get_absolute_url(self):
        return reverse('homepage-detail', args=(self.pk))    
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Home Page'
        verbose_name_plural = 'Home Pages'
   
```

As before, the`GatekeeperSerialAbstractModel` creates the `live_as_of` and `publish_status` fields.   It also creates a `default_live` field.   

## View Code 

The View code becomes:

```
from django.views.generic import DetailView
from gatekeeper.mixins import GatekeeperSerialMixin

class HomepageDetailView(GatekeeperSerialMixin, DetailView):
    model = Homepage
    template_name = 'homepage/homepage_detail.html'
    context_object_name = 'homepage'
```

## Setting up `urls.py`

In the `urls.py` there's a slight twist.  You'll want two entries.

```
from django.urls import path
from .views import HomepageDetailView

urlpatterns = (
    path('', HomepageDetailView.as_view(), name='homepage-live'),
    path('homepage/<int:pk>/', HomepageDetailView.as_view(), name='homepage-detail'),
)
```

## How it works

What's happening behind the scenes:

1. If you are logged into the Admin you can view any Homepage instance (with the `/homepage/<pk>/` URL).
2. However, for the "live" site, we send the `pk`-less URL.
3. The `GatekeeperSerialMixin` mixin - if no PK is provided, will attempt to find the "most approrpiate" instance of the model.

How does it do that?

* Rule 0: Only objects that COULD be in play can play (i.e., `publish_status` cannot be -1)
    
* Rule 1: if your date is in the future, then you can't play
    
* Rule 2: pick from the ones with "date set" that's in the past who have been published (i.e., `live_as_of` is not None)
    
* Rule 3: Barring that - pick the most-recently modified page with `publish_status` = 1
            (this is because it IS possible for a "always on" page to have never gone through
            the publish step with a publish date - it's just FORCED TO BE ON)
    
* Rule 4: Barring THAT - pick the most-recently modified page with `publish_status` != -1 that has `default_live` = True.
            
* Rule 5: Barring THAT - None (and 404).

Note Rule #4 --- this is where the `default_live` field comes into play.   You can define a model instance with `default_live` = True.  This item will be return if no other instance passes the rules.  Basically it's can be a generic "fall back" for the model so that the public page ALWAYS returns something.   Handy!

##  `utils.py` - helper functions

In case you need it, there's a helper function, `get_appropriate_object_from_model` that will return the "live" instance of any serial gatekeeper model:

```
get_appropriate_object_from_model(object_set, is_queryset=False)
```

where object_set is EITHER:

1. a Model that has subclassed `GatekeeperSerialAbstractModel` (and `is_queryset=False`), OR;
2. a query FROM a Model that has subclassed `GatekeeperSerialAbstractModel` (where you send `is_queryset=True`).

# The Admin Interface

Gatekeeper alters the default Admin for models that use it.

## List Display

For the basic gatekeeper, two fields are added to the `list_display` (they'll appear after anything set in the ModelAdmin):

1. A `show_publish_status` that takes the `live_as_of` and `publish_status` fields and creates a human-friendly string from them;
2. A `available_to_public` model property that returns True/False to show "is this available to the public"?

For the "serial" gatekeeper, there are also two fields:

1. `show_publish_status` as before
2. `is_live` - returns True/False to show which item is the one that will appear on the live site.

## Fieldsets

All Gatekeeper-related fields are displayed on the model Admin edit page in a fieldset called "Gatekeeper".

## Admin actions

For convenience in the listing page of the Admin, five Admin actions have been defined:

1. "Revert to Preview/Pending status":   this sets `live_as_of` and `publish_status` to None.   The item is no longer live, and won't go live until these values are changed;
2. "Take Item PERMANENTLY LIVE": this sets `publish_status` = 1 --- the item will be live;
3. "Take Live as of Right Now":  this sets `live_as_of` = "now", and `publish_status` = 0 --- the item will be live;
4. "CONDITIONALLY online using `live_as_of` date": this sets `publish_status = 0` and keeps `live_as_of` to whatever it was before.   You'd use this if you wanted to change a PERMANENTLY LIVE or COMPLETELY OFFLINE setting;
5. "Take item COMPLETELY OFFLINE": this sets `publish_status` = -1 --- the item disappears from the site entirely.

# Testing

There are unit tests for the `can_this_object_page_be_shown`, `can_this_object_page_be_shown_to_public`, and `get_appropriate_object_from_model` utility methods.   Run `python runtests.py`.

# Troubleshooting

## _I have a page that's not live but I can still see it!_

Are you sure you're not logged into the Admin?   If you are, you can still "see" pages that aren't live.

# Features still to be integrated

## Parental Gatekeeping

(To be added from the PBSMM test case)

Sometimes you have a model that has a FK relationship to another model, and you want both of them to be under gate-keeping.   If "parent" model A's gatekeeping should influence model B, you can set things to override model B based upon the settings for model A.

For example, if you have models for Author and Book, you can set it up that if the Author is not live, then NONE of the Books are live either.   This is convenient for sites where you might want to take several pages live all at once.

## "Standalone" items

(To be added from the PBSMM test case)

BUT sometimes you do NOT want the parent model to control its children.   Standalone models will NOT check their parents for permission.

For example you MIGHT want to limit the Books shown for a specific Author EXCEPT for this ONE Book.    So you can set `treat_as_standalone` for that one Book, and depending on the `live_as_of` and `publish_status` settings it will be "live" or not, WITHOUT checking to see what the same values are for that Book's Author.

