from datetime import datetime
import pytz

"""
 THIS IS THE MAIN GATEKEEPER
 
 This controls WHICH records show up on a website, based upon a set of rules.
 
 It returns True or False given:
    1. the requests.user object (which can be None)
    2. one of the PBSMM objects (Episode, Season, Site, Special)

 How this works:

    There are five possible publish states an object can be in.
        1. (publish_status =  1): Object is PERMANANTLY LIVE - think of this as a ALWAYS ON switch
        2. (publish_status =  0): Object is CONDITIONALLY LIVE - the "live_as_of" date is in the past
        3. (publish_status =  0): Object is PENDING LIVE - the "live_as_of" date is still in the future
        4. (publish_status =  0): Object is NOT YET PUBLISHED - the "live_as_of" date is NULL
        5. (publish_status = -1): Object is PERMANENTLY OFFLINE - this is the ALWAYS OFF Switch

 Page requesters can either be logged in to the Django Admin (i.e., staff) or not (i.e., the general public)

    RULE 1:   Objects - when created - start off with publish_status = 0 and live_as_of = None
        This means that the logged-in Admin user can edit the record and "see" the page for Q/A,
            but it is NOT AVAILABLE to the public.

    RULL 2:   Objects ONLY EVER appear to the public (i.e., 'are live') if:
        a. The publish_status = 1 regardless of the live_as_of date
        b. The publish_status = 0 AND the live_as_of date exists and is in the past.

    RULE 3:   Objects with a publish_status of -1 don't appear on the site to ANYONE.

    RULE 4:   Objects are shown on model listing pages to the public ONLY IF:
        a.  The object is "live" (see Rule 2)
        b.  Any PARENT objects ARE ALSO "live" (but see exception below)
        

STANDLONE OBJECTS:

    For objects with the treat_as_standalone field, and where that field == 1, the above rules apply
    EXCEPT FOR Rule 4b:   "standalone" objects do NOT CHECK their parents' publish states.
    
"""

def can_object_page_be_shown(user, this_object, including_parents=False):
    """
    RAD: 4 Oct 2018 --- so a weird condition happened, and I'm not sure what the appropriate
        logic ought to be:
        
        If a STANDALONE Episode has a parental Show that has publish_status = -1, does the episode
        get blocked or not?
        
        On one hand, it should be YES, because if the entire SHOW is "permanently offline", then that
        logically should extend to their children.
        
        On the OTHER HAND, the entire point of "standalone" is "do NOT consult the parents", so it shouldn't
        MATTER what the 
    
    """
    try:
        if user.is_staff: # admin users can always see pages
            if this_object.publish_status >= 0 or this_object.treat_as_standalone == 1:
                return True # I can see everything except specifically turned-off objects because I'm an admin
    except:
        pass # I am not logged in - continue

    if this_object.publish_status == 1: # this object is ALWAYS live
        return True
        
    if not this_object: # this object isn't live or doesn't exist
        return False
    
    # THIS IS CORRECT: even if standaalone is "true" if publish is <0 then do not pass!
    if this_object.publish_status < 0:  # this object isn't live
        return False

    if this_object.publish_status == 0: # this object MIGHT be live
        if this_object.live_as_of is not None:
            now = datetime.now(pytz.utc)
            delta = this_object.live_as_of <= now
            if not delta:
                return False
            #return this_object.live_as_of <= now # if I'm past my publish date it's LIVE, otherwise it's not live yet
        else:
            return False # this object is still being working on - no publish date set yet.

    # DO WE NEED including_parents as a variable?   Can't we just test on treat_as_standalone?
    # Yes, because if we're recursing an episode through its season, then we want to send the EPISODE's
    # state to check the Show, not the parental season.
    
    #### THIS NEEDS TO BE RE-WRITTEN TO BE MADE GENERIC
    #if including_parents:
    #    recurse = False
    #    if this_object.model_object_type == 'pbsmm_episode':
    #        parent = this_object.season
    #        recurse = True
    #    elif this_object.model_object_type == 'pbsmm_special':
    #        parent = this_object.show
    #    elif this_object.model_object_type == 'pbsmm_season':
    #        parent = this_object.show
    #    else:
    #        parent = None
    #
    #    if parent:
    #        return can_object_page_be_shown(user, parent, including_parents=recurse)
        
    return True
    
def can_object_page_be_shown_to_pubilc(this_object):
    return can_object_page_be_shown(None, this_object, including_parents=False)

def get_appropriate_object_from_model(object_set, is_queryset=False):
    """
    Tools:
        - publish_status = {1: always on, 0: conditionally on, -1: always off, NULL never published}
        
        OK - this is how the game is played:
        
        Rule 0: only objects that COULD be in play can play
        Rule 1: if your date is in the future, then you can't play
        Rule 2: pick from the ones with "date set" that's in the past who have been published
            (i.e., live_as_of is not None)
        Rule 3: Barring that - pick the most-recently modified page with publish_status = 1
            (this is because it IS possible for a "always on" page to have never gone through
            the publish step with a publish date - it's just FORCED TO BE ON)
        Rule 4: Barring THAT - pick the most-recently modified page with publish_status != -1 that has
            default_live = True.
        Rule 5: Barring THAT - return the Page that is the default home page (is that even possible)?
            or None
            
    RAD 13-Feb-2019
        I've added an optional arg that allows processing of already-created querysets.
        That way you can have a model that groups instances by a foreign key, and then use the gatekeeper on clump.
    
    """
    now = datetime.now(pytz.utc)

    # Use the whole model by default.
    # Otherwise if is_queryset is True, treat it as a queryset.
    if is_queryset:
        qs = object_set.exclude(publish_status=-1)
    else:
        qs = object_set.objects.exclude(publish_status=-1) 

    # anything that is not available to anyone is ignored
    qs = qs.exclude(live_as_of__gt=now)
    
    # Send most-recent live_as_of
    qs1 = qs.exclude(live_as_of__isnull=True) # For some reason this does NOT WORK
    qs1 = qs.filter(publish_status=0).order_by('-live_as_of').first()
    if qs1:
        return qs1
    
    # Send the most recently updated permanent on    
    try:
        qs2 = qs.filter(publish_status=1).order_by('-date_modified').first()
    except:
        qs2 = qs.filter(publish_status=1).first()
    if qs2:
        return qs2
        
    # Send the most-recent "default"
    try:
        qs3 = qs.filter(default_live=True).order_by('-date_modified').first()
    except:
        qs3 = qs.filter(default_live=True).first()
    if qs3:
        return qs3

    # Nothing is avaialble - this will likely result in a 404 page being returned.
    return None


# TEST CODE FROM SHELL
#from pbsmmapi.abstract.gatekeeper import can_object_page_be_shown
#from pbsmmapi.show.models import PBSMMShow
#ss = PBSMMShow.objects.all()
#from django.contrib.auth.models import User
#user = User.objects.first()
#import pytz
#from datetime import datetime
#future = datetime(2018, 9, 1, 0, 0, 0, 0, pytz.utc)
#past = datetime(2018, 5, 1, 0, 0, 0, 0, pytz.utc)
#now = datetime.now(pytz.utc)

#for s in ss:
#    s.live_as_of = past
    
#ss[10].live_as_of = None
#ss[11].live_as_of = future
#ss[7].publish_status = 1
#ss[6].publish_status = -1

#for s in ss:
#   can_object_page_be_shown(None, s)
#   can_object_page_be_shown(user, s)