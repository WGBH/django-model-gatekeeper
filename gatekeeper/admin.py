from django.contrib import admin
from django.utils.safestring import mark_safe
import pytz
from datetime import datetime
from .utils import get_appropriate_object_from_model

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

    Because of the Python MRO, you can't put the typical ModelAdmin methods here, because
    if you have >1 abstract baseclasses to your ModelAdmin, the Python MRO will stop at the
    first instance of the method, e.g.:
    
        class Foo1(admin.ModelAdmin):
            def get_readonly_fields(self, obj=None):
                return self.readonly_fields + ('foo1_field')
        class Foo2(admin.ModelAdmin):
            def get_readonly_fields(self, obj=None):
                return self.readonly_fields + ('foo2_field')
        class MyModel(Foo1, Foo2):
            pass
    
    will stop at Foo1, and never get to Foo2.
    
    To get around this, there are "helper methods" in admin_helpers.py, you'll still have
    to create methods in your ModelAdmin classes using either GatekeeperGenericAdmin or
    GatekeeperSerialAdmin but you can call these from there to get the desired behavior.
    """
    
    ### Custom methods
    def gatekeeper_show_publish_status(self, obj):
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
    gatekeeper_show_publish_status.short_description = 'Pub. Status'
    
    ### Control functions
    # These five operations are added to the admin listing page 
    def gatekeeper_set_to_default(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.live_as_of = None
            item.save()
    gatekeeper_set_to_default.short_description = 'Revert to Preview/Pending status.'
    
    def gatekeeper_permanently_online(self, request, queryset):
        for item in queryset:
            item.publish_status = 1
            item.save()
    gatekeeper_permanently_online.short_description = 'Take item PERMANTENTLY LIVE'
    
    def gatekeeper_conditionally_online(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.save() 
    gatekeeper_conditionally_online.short_description = 'CONDITIONALLY Online using live_as_of Date'
           
    def gatekeeper_take_online_now(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.live_as_of = datetime.now(pytz.utc)
            item.save()
    gatekeeper_take_online_now.short_description = 'Take Live as of Right Now'
    
    def gatekeeper_take_offline(self, request, queryset):
        for item in queryset:
            item.publish_status = -1
            item.save() 
    gatekeeper_take_offline.short_description = 'Take item COMPLETELY OFFLINE'
    
    #class Meta:
    #    abstract = True
        
class GatekeeperSerialAdmin(GatekeeperGenericAdmin):
    """
    This superclass extends the previous one by adding the default_live field, and adds an is_live() method
    to allow the user to see which object in a model is determined to be the "live" page.
    
    Everything else is the same as above.
    """
        
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
    def gatekeeper_show_publish_status(self, obj):
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
    gatekeeper_show_publish_status.short_description = 'Pub. Status'
