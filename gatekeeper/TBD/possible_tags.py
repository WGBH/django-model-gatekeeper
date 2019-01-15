    
    def __is_publicly_available(self):
        """
        THIS IS ONLY TO BE USED IN TEMPLATES.
        It RELIES on the gatekeeper - so using it in front of the gatekeeper is counter-productive.
        (I made this mistake, thinking I was taking a shortcut.   It cost me a day's work.   Don't be
        like me.)
        
        RAD 4 Oct 2018
        """
        # can_object_page_be_shown is the site gatekeeper.
        # if the user is None (as is called here) that means "not logged into the Amdin": i.e., the general public.
        try:
            if self.treat_as_standalone == 0:
                return can_object_page_be_shown(None, self, including_parents = True)
        except:
            pass
            
        return can_object_page_be_shown(None, self, including_parents = False)
    is_publicly_available = property(__is_publicly_available)