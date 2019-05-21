
BASIC_FIELDS  = ((('publish_status', 'show_publish_status', 'available_to_public'), 'live_as_of', ))
SERIAL_FIELDS = ((('publish_status', 'show_publish_status', 'is_live'), 'live_as_of', 'default_live'))

def gatekeeper_add_to_readonly_fields():
    return ('is_live', 'shoe_publish_status')
    
def gatekeeper_add_to_fieldsets(section=True, show_description=False, collapse=False, serial=False):
    if serial:
        fields = SERIAL_FIELDS
    else:
        fields = BASIC_FIELDS
        
    description = None
    if show_description:
        description = 'This is the description for Package 1'
    if section:
        return ('Package 1', {
            'fields': fields,
            #'collapse': collapse,
            'description': description
        })
    return fields
    
def gatekeeper_add_to_list_display(serial=False):
    if serial:
        return 'show_publish_status', 'is_live', 'default_live']
    return ['show_publish_status','available_to_public']
    
