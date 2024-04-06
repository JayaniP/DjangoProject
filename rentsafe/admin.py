from django.contrib import admin
from .models import PropertyDetail, ClaimDetail, RentalAgencyProfile, Transaction, ClientDetail, Payment
from django.utils.safestring import mark_safe 
import os
from django.conf import settings 

# Register your models here.

@admin.register(PropertyDetail)
class PropertyDetailAdmin(admin.ModelAdmin):
    fields = ('rental_agency_id', 'name','description','details','daily_price', 'deposit',
              'image1','image2','image3','image4','property_status')

    def image_preview(self, obj):
        return mark_safe('<img src="{}" width="100" height="100" />'.format(obj.my_image_field.url)) 
    image_preview.short_description = 'Image Preview' 


@admin.register(ClaimDetail)
class ClaimDetailAdmin(admin.ModelAdmin):
    list_display = [
        'ref_number', 'name', 'contact', 'email', 'address','management_email',
        'cname', 'ccontact','cemail','start_date','end_date',
        'quote_deatils','statement_description','pictures_description', 'damage_evidence','police_report', 'claim_status'] 
    search_fields = ['ref_number']
    list_filter = ['claim_status']
    list_editable = ['claim_status']

    def save(self, *args, **kwargs):
        for field in ['quote_details', 'statement_description', 'pictures_description', 'damage_evidence', 'police_report']:  
            if getattr(self, field):  # If the document field has a value
                full_filename = os.path.join(settings.MEDIA_ROOT, getattr(self, field).name)
                setattr(self, field, full_filename)  # Update the path
        super().save(*args, **kwargs)  # Call the original save behavior


@admin.register(RentalAgencyProfile)
class RentalAgencyAdmin(admin.ModelAdmin):
    list_display = [
        'unique_id', 'agencyname',  'username', 'email', 'address', 'contact', 'stripe_account_id','failed_login_attempts'] 
    
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['booking_reference_number', 'client',  'property_id',
                     'deposit_amount', 'rental_amount', 'total_amount', 'status', 'stripe_charge_id'] 
    
@admin.register(ClientDetail)
class ClientDetailAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'contact', 'evidence_proof'] 

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_reference_number', 'deposit_amount', 'rental_amount', 'total_amount',
                    'status','stripe_charge_id','payment_intent_id'] 
