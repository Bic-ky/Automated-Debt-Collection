from django.db import models
from account.models import User
from django.utils import timezone

class Client(models.Model):
    short_name = models.CharField(max_length=255, unique=True , null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pan_number = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(
        max_digits=10,  
        decimal_places=2,
        null=True,
        blank=True,
        default=0
    )

    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email=models.EmailField(null=True,blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    
    GROUP_CHOICES = (
    ('Advanced', 'Advanced'),
    ('Normal', 'Normal'),
    )

    group = models.CharField(max_length=100, choices=GROUP_CHOICES, null=True, blank=True, default='Normal')
    collector = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': User.USER}, related_name='clients', null=True, blank=True)
    guarantee_world_insurer = models.CharField(max_length=255, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=15,default=0, decimal_places=2, null=True, blank=True)
    overdue120=models.FloatField(null=True, blank=True,default=0)
    grant_period=models.FloatField(default=0)


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
    cycle1 = models.FloatField(null=True, blank=True,default=0)
    cycle2 = models.FloatField(null=True, blank=True,default=0)
    cycle3 = models.FloatField(null=True, blank=True,default=0)
    cycle4 = models.FloatField(null=True, blank=True,default=0)
    cycle5 = models.FloatField(null=True, blank=True,default=0)
    cycle6 = models.FloatField(null=True, blank=True,default=0)
    cycle7 = models.FloatField(null=True, blank=True,default=0)
    cycle8 = models.FloatField(null=True, blank=True,default=0)
    cycle9 = models.FloatField(null=True, blank=True,default=0)
    balance = models.FloatField(null=True, blank=True,default=0)
    short_name = models.ForeignKey(Client, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        if self.bill_no:
            return self.bill_no
        else:
            account_name = self.short_name.account_name if self.short_name else None
            return account_name or f"Bill {self.pk}"  # You can customize this fallback representation
    
class Action(models.Model):
    action_date = models.DateField()
    TYPE_CHOICES = (
        ('auto', 'auto'),
        ('manual', 'manual'),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    SMS_CHOICES = (
        ('Reminder', 'Reminder'),
        ('Gentle', 'Gentle'),
        ('Strong', 'Strong'),
        ('Final', 'Final'),
    )
    ACTION_CHOICES = (
        ('SMS', 'SMS'),
        ('Email', 'Email'),
        ('Call', 'Call'),
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_amount = models.FloatField()
    short_name = models.ForeignKey(Client, on_delete=models.CASCADE)
    subtype = models.CharField(max_length=20, choices=SMS_CHOICES, null=True, blank=True)
    followup_date = models.DateField(blank=True, default=None, null=True)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    pause = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True,)

    def __str__(self):
        return f"{self.action_type} on {self.action_date} "


class DailyBalance(models.Model):
    collector = models.ForeignKey(User, on_delete=models.CASCADE)
    total_balance = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.collector.full_name} - {self.date}"

    class Meta:
        unique_together = ['collector', 'date']
    

    

