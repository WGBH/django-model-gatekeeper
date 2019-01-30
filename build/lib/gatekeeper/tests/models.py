from django.db import models
from ..models import GatekeeperAbstractModel, GatekeeperSerialAbstractModel

class GatekeeperArticleTestModel(GatekeeperAbstractModel):
    title = models.CharField(max_length=100, null=False)
    
class GatekeeperHomepageTestModel(GatekeeperSerialAbstractModel):
    title = models.CharField(max_length=100, null=False)
    
