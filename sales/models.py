from django.db import models
from account.models import User

class Client(models.Model):
    short_name = models.CharField(max_length=255, unique=True , null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pan_number = models.CharField(max_length=20, null=True, blank=True)
    balance = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    
    group = models.CharField(max_length=100, null=True, blank=True)
    collector = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.USER}, related_name='clients', null=True, blank=True)
    guarantee_world_insurer = models.CharField(max_length=255, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)


    def __str__(self):
        if self.account_name:
            return self.account_name
        elif self.short_name:
            return self.short_name
        else:
            return f"Client {self.pk}"  # You can customize this fallback representation