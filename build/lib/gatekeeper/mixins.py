import pytz
from datetime import datetime

from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from .utils import can_object_page_be_shown, get_appropriate_object_from_model

"""

These are the View mixins for Gatekeeper objects.
They apply the gatekeeper rules.
See the documentation in gatekeeper.py for details.

"""
class GatekeeperAuthenticationMixin(ContextMixin):
    """
    These are done for all the Listing and Detail pages...
    It just creates an extra variable in the context to say whether the user is logged into the Admin or not.
    Aren't mixins just freaking cool?
    """
    def get_context_data(self, **kwargs):
        context = super(GatekeeperAuthenticationMixin, self).get_context_data(**kwargs)
        context['is_logged_in'] = self.request.user.is_authenticated
        return context

class GatekeeperListMixin(MultipleObjectMixin, GatekeeperAuthenticationMixin):
    """
    This is for Listing views that apply to all object ListView classes.
    """
    def get_queryset(self):
        qs = super(GatekeeperListMixin, self).get_queryset()
        
        # No one can see objects with publish_status < 0
        qs = qs.exclude(publish_status__lt=0)
        
        # If you're logged in you can see everything else.
        user = self.request.user
        if not user.is_authenticated:
            # If you are not logged in, then live_as_of must exist (not None) and must be in the past.
            condition_1 = Q(publish_status=0)
            condition_2 = Q(live_as_of__gt=datetime.now(pytz.utc))
            condition_3 = Q(live_as_of__isnull=True)
            qs = qs.exclude(condition_1 & condition_2)
            qs = qs.exclude(condition_1 & condition_3)
        return qs

class GatekeeperDetailMixin(SingleObjectMixin, GatekeeperAuthenticationMixin):
    """
    This is for detail views that apply to all object DetailView classes.
    
    WE CANNOT USE the "available_to_public" property as a quick, "simple" workaround because you have to be able
    to reliably send the self.request.user to the gatekeeper (available_to_public is really only supposed
    to be used as a test within TEMPLATES, i.e., AFTER the gatekeeper has done its job!)
    """
    def get_object(self, queryset=None):
        obj = super(GatekeeperDetailMixin, self).get_object(queryset=queryset)
        user = self.request.user
        
        #### This code needs to be re-integrated if parental object gatekeeping is a feature we want to have.
        #try:
        #    if obj.treat_as_standalone == 0:
        #        #print "MIXIN CHECK PARENT: ", can_object_page_be_shown(user, obj, including_parents=True)
        #        if can_object_page_be_shown(user, obj, including_parents=True):
        #            return obj
        #    else:
        #        #print "MIXIN STANDALONE: ", can_object_page_be_shown(user, obj, including_parents=False)
        #        if can_object_page_be_shown(user, obj, including_parents=False):
        #            return obj
        #except:
            #print "MIXIN HAS NO STANDALONE: ", can_object_page_be_shown(user, obj, including_parents=False)
        if can_object_page_be_shown(user, obj, including_parents=False):
            return obj

        raise Http404()
            
class GatekeeperSerialMixin(SingleObjectMixin, GatekeeperAuthenticationMixin):
    """
    This handles serial filtering.   What I mean by this:
        Models using this mixin are assumed to only have one instance of the object "live" at any given time.
        Therefore the gatekeeper is used against all of the instances of the model to find the "right"
        instance to return.
        
        A good example of this is a Homepage app where the content producer can stage multiple instances of the
        homepage to go live at different times.
    """
        
    def get_object(self, queryset=None):
        """
        Note that we do NOT call super() here!
        If you DO then the request for the "generic" page will FAIL because no PK or Slug is sent with the request!
        It's BECAUSE this get_object() looks for "the" appropriate object, that we don't want the SingleObjectMixin's
        get_object() to run AT ALL.
        """

        if self.kwargs.get('pk') and self.request.user.is_staff:
            result = get_object_or_404(self.model, id=self.kwargs.get('pk'))
        else:
            winner = get_appropriate_object_from_model(self.model)
            if winner:
                id = winner.id
            else:
                id = None
            result = get_object_or_404(self.model, id=id)
        return result