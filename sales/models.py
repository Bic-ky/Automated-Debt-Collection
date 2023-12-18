from django.db import models
from account.models import User

class Client(models.Model):
    short_name = models.CharField(max_length=255, unique=True , null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pan_number = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(
        max_digits=10,  
        decimal_places=2,
        null=True,
        blank=True
    )

    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email=models.EmailField(null=True,blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    
    group = models.CharField(max_length=100, null=True, blank=True)
    collector = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.USER}, related_name='clients', null=True, blank=True)
    guarantee_world_insurer = models.CharField(max_length=255, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    overdue120=models.FloatField(null=True, blank=True)


    def __str__(self):
        if self.account_name:
            return self.account_name
        elif self.short_name:
            return self.short_name
        else:
            return f"Client {self.pk}"  # You can customize this fallback representation
        


class Bill(models.Model):
    type = models.CharField(max_length=40,blank=True,null=True)
    bill_no = models.CharField(max_length=40, blank=True)
    due_date = models.DateField(null=True, blank=True)
    inv_amount = models.FloatField(null=True, blank=True)
    cycle1 = models.FloatField(null=True, blank=True)
    cycle2 = models.FloatField(null=True, blank=True)
    cycle3 = models.FloatField(null=True, blank=True)
    cycle4 = models.FloatField(null=True, blank=True)
    cycle5 = models.FloatField(null=True, blank=True)
    cycle6 = models.FloatField(null=True, blank=True)
    cycle7 = models.FloatField(null=True, blank=True)
    cycle8 = models.FloatField(null=True, blank=True)
    cycle9 = models.FloatField(null=True, blank=True)
    balance = models.FloatField(null=True, blank=True)
    short_name = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        account_name = self.short_name.account_name if self.short_name else None
        return account_name or f"Bill {self.pk}"  # You can customize this fallback representation
    
class Action(models.Model):
    action_date=models.DateField()
    TYPE_CHOICES = (
        ('auto','auto'),
        ('manual','manual'),
        )
    type =models.CharField(max_length=20, choices=TYPE_CHOICES)
    ACTION_CHOICES = (
        ('SMS','SMS'),
        ('Email','Email'),
        ('Call','Call'), 
        )
    action_type =models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_amount= models.FloatField()
    short_name = models.ForeignKey(Client, on_delete=models.CASCADE)
    bill_no = models.CharField(max_length=40, blank=True)
