from .models import GatekeeperHomepageTestModel
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
import pytz

from gatekeeper.utils import get_appropriate_object_from_model

class GatekeeperHomepageTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username='gktest',
            email='test@test.com',
            password='1@3$5',
        )
        now = datetime.now(pytz.utc)
        last_week = now - timedelta(days=7)
        earlier = now - timedelta(days=15)
        later = now + timedelta(days=7)
        wayback = now - timedelta(days=30)
        # Test cases
        # 1. In Progress - not live
        cls.a01 = GatekeeperHomepageTestModel.objects.create(pk=1, title='Test 1: pending') 
        # 2. Fallback: default_live = True 
        cls.a02 = GatekeeperHomepageTestModel.objects.create(pk=2, title='Test 2: always on, fallback', 
            publish_status = 1, default_live = True) 
        # 3. Taken offline - not live
        cls.a03 = GatekeeperHomepageTestModel.objects.create(pk=3, title='Test 3: offline', 
            live_as_of = earlier, publish_status = -1) 
        # 4. Was live - overridden by newer homepage
        cls.a04 = GatekeeperHomepageTestModel.objects.create(pk=4, title='Test 4: out of date', 
            live_as_of = earlier) 
        # 5. Is live now
        cls.a05 = GatekeeperHomepageTestModel.objects.create(pk=5, title='Test 5: should be live', 
            live_as_of = last_week)
        # 6. Not live yet
        cls.a06 = GatekeeperHomepageTestModel.objects.create(pk=6, title='Test 6: future home page ready to go',
            live_as_of = later) 
        
    def setUp(self):
        self.client.login(username='gktest', password='1@3$5')
        
    def test_which_page_is_live(self):
        """
        Given the data above, this should be #5
        """
        live_pk = 5
        hp = get_appropriate_object_from_model(GatekeeperHomepageTestModel)
        print ("Testing Home page selection: got ", hp, hp.title)
        self.assertEqual(hp.pk, 5)
        
    