from django.db import models
from account.models import User

# Create your models here.
class Client(models.Model):
    vat_number = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    address = models.TextField()
    group= models.CharField(max_length=100)
    collector = models.ForeignKey(User, on_delete=models.CASCADE,limit_choices_to={'role': User.USER}, related_name='clients')
    guarantee_world_insurer = models.CharField(max_length=255)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2)


    def _str_(self):
        return self.name