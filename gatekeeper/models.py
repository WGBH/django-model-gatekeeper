from django.db import models
from django.utils.translation import ugettext_lazy as _
from .utils import can_object_page_be_shown_to_pubilc

PUBLISH_STATUS_LIST = (
    (-1, 'NEVER Available'),
    (0, 'USE "Live as of Date"'),
    (1, 'ALWAYS Available')
)

"""
There are two different types of models that use gatekeeping:

    1. GatekeeperAbstractModel:
        Models that have individual objects, where each one is handled separately.
        e.g., the objects in an Article model may be live, might be waiting for their
            live_as_of date to happen, might be in preparation, or might be turned off.
            
        For these models,  is_serial = False (default)
            
    2. GatekeeperSerialAbstractModel:
        Models where only ONE object is meant to be live at any time.
        e.g., a Homepage model might have several "queued up" to go live at any given time.
        
        For these models,  is_serial = True, and there is an extra field for default_live
            which is used if the logic doesn't return any particular object.
        
"""

class GatekeeperAbstractModel(models.Model):
    publish_status = models.IntegerField (
        _('Publish Status'),
        default = 0, null = False,
        choices = PUBLISH_STATUS_LIST
    )
    ###
    ### live_as_of starts out as NULL 
    ### meaning "I am still being worked on" (if publish_status == 0)
    ### OR "I have deliberately been pushed live (if publish_status == 1)"
    ###
    ### if set, then after that date/time the object is "live".
    ###
    ### This allows content producers to 'set it and forget it'.
    ###
    live_as_of = models.DateTimeField (
        _('Live As Of'),
        null = True, blank = True,
        help_text = 'You can Set this to a future date/time to schedule availability.'
    )
    ### this determined the behavior of the gatekeeping
    is_serial = False
    
    ### This sets up the ability for gatekeeping hierarchies.
    parental_model_field = None
    
    def __available_to_public(self):
        return can_object_page_be_shown_to_pubilc(self)
    available_to_public = property(__available_to_public)
    
    class Meta:
        abstract = True

class GatekeeperSerialAbstractModel(GatekeeperAbstractModel):
    default_live = models.BooleanField (
        _('Default as Live'), default = False,
        help_text = "If everything else fails, then return this as the live home page"
    )
    is_serial = True
    
    class Meta:
        abstract = True