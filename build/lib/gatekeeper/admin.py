from django.contrib import admin
from django.utils.safestring import mark_safe
import pytz
from collections import OrderedDict
from datetime import datetime
from .utils import get_appropriate_object_from_model

BASIC_FIELDS  = ((('publish_status', 'show_publish_status', 'available_to_public'), 'live_as_of', ))
SERIAL_FIELDS = ((('publish_status', 'show_publish_status', 'is_live'), 'live_as_of', 'default_live'))

def reset_fieldsets(orig, new):
    """
    This is just to re-write the fieldsets parameters with the gatekeeper section.
    For some reason doing it any other way throws an error...   Oh well.
    """
    fs = []
    if orig:
        for f in orig:
            fs.append(f)
            fs.append(new)
    return fs
    
def is_in_the_future(dt):
    """
    Is this (UTC) date/time value in the future or not?
    """
    if dt > datetime.now(pytz.utc):
        return True
    return False

class GatekeeperGenericAdmin(admin.ModelAdmin):
    """
    This superclass incorporates the gatekeeper fields into the Django Admin.
    It has a custom get_fieldsets (to update the model admin with the gatekeeper fields).
    """
    actions = ['set_to_default', 'permanently_online', 'take_online_now', 'conditionally_online', 'take_offline', ]
    
    def get_fieldsets(self, request, obj=None):
        """
        Add a section to the fieldsets for the fields used by the gatekeeper.
        """
        gatekeeper_fieldset_entry = ['Gatekeeper', { 'fields': BASIC_FIELDS, }]
        return reset_fieldsets(self.fieldsets, gatekeeper_fieldset_entry)
        
    def get_list_display(self, request):
        """
        The default will be to add show_publish_status and is_live to the list_display.
        One can turn this off by making a custom get_list_display.
        """
        x = self.list_display
        if x is None:
            x = ['pk',]
        return x + ['show_publish_status','available_to_public']
    
    def get_readonly_fields(self, request, obj=None):
        """
        Add these to the readonly_fields so that they can be used within the admin.
        """
        before = list(self.readonly_fields)
        mine = ['show_publish_status','available_to_public']
        return before + mine
        
    def get_actions(self, request):
        actions = super(GatekeeperGenericAdmin, self).get_actions(request)
        return actions
        
    ### Custom methods
    def show_publish_status(self, obj):
        """
        This creates an HTML string showing a object's gatekeeper status in a user-friendly way.
        """
        if obj.publish_status > 0:
            return mark_safe("<span style=\"color: #0c0;\"><b>ALWAYS</b></span> Available")
        elif obj.publish_status < 0:
            return mark_safe("<span style=\"color: #c00;\"><B>NEVER</b></span> Available")
        else: # it EQUALS zero
            if obj.live_as_of is None:
                return "Never Published"
            else:
                dstr = obj.live_as_of.strftime("%x")
                if is_in_the_future(obj.live_as_of):
                    return mark_safe("<b>Goes LIVE: %s</b>"% dstr)
                else:
                    return mark_safe("<B>LIVE</B> <span style=\"color: #999;\">as of: %s</style>" % dstr)
        return "???"
    show_publish_status.short_description = 'Pub. Status'
    
    ### Control functions
    # These five operations are added to the admin listing page 
    def set_to_default(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.live_as_of = None
            item.save()
    set_to_default.short_description = 'Revert to Preview/Pending status.'
    
    def permanently_online(self, request, queryset):
        for item in queryset:
            item.publish_status = 1
            # WORLD-299 - should this also set live_as_of to the current date/time?
            item.save()
    permanently_online.short_description = 'Take item PERMANTENTLY LIVE'
    
    def conditionally_online(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.save() 
    conditionally_online.short_description = 'CONDITIONALLY Online using live_as_of Date'
           
    def take_online_now(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.live_as_of = datetime.now(pytz.utc)
            item.save()
    take_online_now.short_description = 'Take Live as of Right Now'
    
    def take_offline(self, request, queryset):
        for item in queryset:
            item.publish_status = -1
            item.save() 
    take_offline.short_description = 'Take item COMPLETELY OFFLINE'
    
    ### Custom methods

    class Meta:
        abstract = True
        
class GatekeeperSerialAdmin(GatekeeperGenericAdmin):
    """
    This superclass extends the previous one by adding the default_live field, and adds an is_live() method
    to allow the user to see which object in a model is determined to be the "live" page.
    """
    def get_fieldsets(self, request, obj=None):
        """
        The default will be to add show_publish_status and is_live to the list_display.
        One can turn this off by making a custom get_list_display.
        """
        gatekeeper_fieldset_entry = ['Gatekeeper', {'fields': SERIAL_FIELDS, }]
        return reset_fieldsets(self.fieldsets, gatekeeper_fieldset_entry)

    def get_list_display(self, request):
        """
        The default will be to add show_publish_status and is_live to the list_display.
        One can turn this off by making a custom get_list_display. 
        """
        x = self.list_display
        if x is None:
            x = ['pk',]
        else:
            x = list(x)
        return x + ['show_publish_status', 'is_live', 'default_live']
        
    def get_readonly_fields(self, request, obj=None):
        """
        Add these to the readonly_fields so that they can be used within the admin.
        """
        return self.readonly_fields + ('is_live','show_publish_status')
        
    ### Custom methods
    def is_live(self, obj):
        """
        This shows WHICH object will be the live object.
        Returns True/False.
        
        This is used in the default list_display.
        """
        most_appropriate_object = get_appropriate_object_from_model(self.model)
        if most_appropriate_object == obj:
            return True
        return False
        
    ### Custom methods
    def show_publish_status(self, obj):
        """
        This creates an HTML string showing a object's gatekeeper status in a user-friendly way.
        """
        if obj.publish_status > 0:
            return mark_safe("<span style=\"color: #0c0;\"><b>ALWAYS</b></span> Available")
        elif obj.publish_status < 0:
            return mark_safe("<span style=\"color: #c00;\"><B>NEVER</b></span> Available")
        else: # it EQUALS zero
            if obj.live_as_of is None:
                return "Never Published"
            else:
                dstr = obj.live_as_of.strftime("%x")
                if is_in_the_future(obj.live_as_of):
                    return mark_safe("<b>Goes LIVE: %s</b>"% dstr)
                else:
                    return mark_safe("<B>LIVE</B> <span style=\"color: #999;\">as of: %s</style>" % dstr)
        return "???"
    show_publish_status.short_description = 'Pub. Status'
