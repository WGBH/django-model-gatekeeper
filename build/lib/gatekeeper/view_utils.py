from django.db.models import Q
import pytz
from datetime import datetime

def view_gatekeeper(qs, is_auth, ignore_standalone=False):
    """
    This is here because there are several places in other views that need to create partial querysets
    that are combined (e.g., on the Watch page, but also on the other episodic pages for things like "More from...").
    To make THAT work, you need to know which of those potentially associated objects are actually available on
    the site.
    
    This DOES take Adminsitrative login into account (if is_auth == True), in which case the queryset is passed 
    through unchecked.

    RAD - 2018-Aug-23
    """
    if not is_auth:
        # If you are not logged in, then live_as_of must exist (not None) and must be in the past.
        condition_0 = Q(publish_status__lt=0)
        condition_1 = Q(publish_status=0) 
        condition_2 = Q(live_as_of__gt=datetime.now(pytz.utc))
        condition_3 = Q(live_as_of__isnull=True)
        qs = qs.exclude(condition_0) # publish_status cannot be < 0
        qs = qs.exclude(condition_1 & condition_2)  # if live_as_of is set it must be in the past
        qs = qs.exclude(condition_1 & condition_3)  # if live_as_of is not set and publish_status = 0, must skip
    return qs
    
def object_gatekeeper(obj, is_auth, ignore_standalone=False):
    """
    It's OK to use available_to_public here because the underlying logic is identical.
    """
    if not obj:
        return False
    if is_auth:
        return True
    else:
        try:
            return obj.available_to_public
        except:
            pass
    return False
