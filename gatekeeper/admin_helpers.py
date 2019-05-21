
BASIC_FIELDS  = ((('publish_status', 'show_publish_status', 'available_to_public'), 'live_as_of', ))
SERIAL_FIELDS = ((('publish_status', 'show_publish_status', 'is_live'), 'live_as_of', 'default_live'))

GATEKEEPER_ACTIONS = [
    'gatekeeper_set_to_default', 
    'gatekeeper_permanently_online', 
    'gatekeeper_take_online_now', 
    'gatekeeper_conditionally_online', 
    'gatekeeper_take_offline', 
]

def gatekeeper_add_to_readonly_fields(serial=False):
    """
    This adds the gatekeeper fields to the readonly_fields list.
    
    Usage (in your model admin):
        def get_readonly_fields(self, obj=None):
            return self.readonly_fields + gatekeeper_add_to_readonly_fields()
    """
    f = ['show_publish_status']
    if serial:
        f += ['default_live', 'is_live']
    else:
        f.append('available_to_public')
    return f
    
def gatekeeper_add_to_fieldsets(section=True, collapse=False, serial=False):
    """
    Adds gatekeeper fields to your ModelAdmin fieldsets.
    Options:
        Section: you can add the fields either as it's own section or as part of a section.
        Collapse: whether the section should be collapsable or not.
        
    How to use:
        # section = False
        fieldsets = (
            (None, { 'fields': ( ('pk',), gatekeeper_add_to_fieldsets(section=False), ), }), 
        )

        # section = True
        fieldsets = (
            (None, { 'fields': ( ('pk',), ), }),
            gatekeeper_add_to_fieldsets(section=True),
        )
    """
    if serial:
        fields = SERIAL_FIELDS
    else:
        fields = BASIC_FIELDS
        
    if section:
        if collapse:
            d = {'classes': ('collapse',), 'fields': fields, }
        else:
            d = {'fields': fields, }   
        s = ('Gatekeeper', d)
        return s
    return fields
    
def gatekeeper_add_to_list_display(serial=False):
    """
    This adds fields to list_display for the Admin changelist page for the model.
    """
    if serial:
        return ['show_publish_status', 'is_live', 'default_live']
    return ['show_publish_status','available_to_public']
    
def gatekeeper_add_to_actions():
    """
    This adds the methods for the Admin actions.
    """
    return GATEKEEPER_ACTIONS