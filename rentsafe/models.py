from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils import timezone
from datetime import date 
import uuid
from django import forms


# Create your models here.
class RentalAgencyProfile(AbstractUser):
   # user = models.ForeignKey(User, on_delete=models.CASCADE)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    agencyname = models.CharField(max_length=128, default='default')
    username = models.CharField(max_length=128, default='default')
    email = models.EmailField(default='default@email.com')
    url =  models.TextField()
    address = models.TextField()
    contact = models.CharField(max_length=20)
    password = models.CharField(max_length=128, default='12345')
    failed_login_attempts = models.IntegerField(default=0)
    reset_password_token = models.CharField(max_length=100, null=True, blank=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)

    # Add related_name arguments to the groups and user_permissions fields
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='%(app_label)s_%(class)s_set',
        related_query_name='%(app_label)s_%(class)ss',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='%(app_label)s_%(class)s_set',
        related_query_name='%(app_label)s_%(class)ss',
    )

class ClientDetail(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField(default='default@email.com')
    contact = models.IntegerField(default = 0) 
    evidence_proof = models.FileField(default= None) 

class RentalAgency(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    #unique_id = models.IntegerField(default=1001)  
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact = models.CharField(max_length=20)
    email = models.EmailField()
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
   # number_of_properties = models.IntegerField(blank=True, null=True)

   
class PropertyDetail(models.Model):
    rental_agency_id = models.ForeignKey(RentalAgencyProfile, on_delete=models.CASCADE, null=True,blank=True)
    name = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    details = models.TextField(blank=True)
    daily_price = models.IntegerField(null=True, blank=True)
    deposit = models.IntegerField(null=True, blank=True)
   # start_datetime = models.DateTimeField(default=timezone.now)
  #  end_datetime = models.DateTimeField(default=timezone.now)
    image1 = models.ImageField(blank=True, null=True,upload_to="property/")
    image2 = models.ImageField(blank=True, null=True, upload_to="property/")
    image3 = models.ImageField (blank=True, null=True, upload_to="property/")
    image4 = models.ImageField(blank=True,  null=True, upload_to="property/")
    STATUS_CHOICES = [
        ('AC', 'Active'),
        ('AV', 'Available')
    ]
    property_status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])


class Transaction(models.Model): 
    booking_reference_number = models.CharField(max_length=12, unique=True, editable=False)
    client = models.ForeignKey(ClientDetail, on_delete=models.CASCADE)
    property_id = models.ForeignKey(PropertyDetail, on_delete=models.CASCADE)  # Replace with your model name
    deposit_amount = models.IntegerField()
    rental_amount= models.IntegerField()
    total_amount = models.IntegerField() 
    status = models.CharField(max_length=50, choices=[('Initiated', 'Initiated'), ('Completed', 'Completed')])
    stripe_charge_id = models.CharField(max_length=100, blank=True)

class ClaimDetail(models.Model):
    ref_number = models.CharField(max_length=12, unique=True, editable=False)
    booking_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='claims', blank=True, null=True)
    client = models.ForeignKey(ClientDetail, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=80)
    contact = models.IntegerField(default = 0) 
    email = models.EmailField(default='default@email.com')
    address = models.TextField(null=True)
    management_email = models.EmailField(default='default@email.com')

    cname = models.CharField(max_length=80)
    ccontact = models.IntegerField(default = 0)
    cemail = models.EmailField(default='default@email.com')
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(default=date.today)

    quote_deatils = models.FileField(default= None, upload_to="claim_docs/") 
    statement_description = models.FileField(default= None, upload_to="claim_docs/") 
    pictures_description = models.FileField(default= None, upload_to="claim_docs/")
    damage_evidence = models.FileField(default= None, upload_to="claim_docs/") 
    police_report = models.FileField(default= None, upload_to="claim_docs/") 

    STATUS_CHOICES = [
        ('AC', 'Active'),
        ('RI', 'Review'),
        ('RE', 'Resolved'),
        ('AR', 'Archieved')
    ]
    claim_status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])

class Payment(models.Model):
    payment_reference_number = models.CharField(max_length=12, unique=True, editable=False)
    deposit_amount = models.IntegerField()
    rental_amount= models.IntegerField()
    total_amount = models.IntegerField() 
    status = models.CharField(max_length=50, choices=[('Initiated', 'Initiated'), ('Completed', 'Completed')])
    stripe_charge_id = models.CharField(max_length=100, blank=True)
    payment_intent_id = models.CharField(max_length=100, blank=True)
