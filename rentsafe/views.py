from datetime import timezone
import math
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login, logout
from rentsafe.models import RentalAgencyProfile, PropertyDetail, ClaimDetail, ClientDetail, RentalAgency, Transaction, Payment  
from django.core.mail import send_mail, get_connection
from django.urls import reverse
from django.conf import settings
from django.http import Http404
import random
from django.http import JsonResponse, HttpResponse,  HttpResponseBadRequest
from django.shortcuts import get_list_or_404, get_object_or_404
import zipfile
import io
from django.contrib.auth.decorators import login_required
import stripe
from django.views.decorators.csrf import csrf_exempt
from rentsafe.forms import PropertyDetailForm
from django.core.exceptions import ObjectDoesNotExist 
import datetime  
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY


def signup(request):
    if request.method == "POST":
        agency_name = request.POST.get("agencyname")
        username = request.POST["username"]
        email = request.POST["email"]
        address = request.POST.get("address")
        contact = request.POST.get("contact")
        password = request.POST["password"]

      #  if User.objects.filter(username=username):
           # messages.error(request,"This name is already exists, please try other name!")
           # return redirect('signup')

        if RentalAgencyProfile.objects.filter(email=email):
            messages.error(request,"This email is already registered!")
            return redirect('signup')
        
      #  if not username.isalnum():
         #   messages.error(request,"Name must be in alpha numeric!")
           # return redirect('signup')

        user = RentalAgencyProfile.objects.filter(email = email)

        if user.exists():
            messages.info(request, 'User already exists!')
            return redirect('signup')


         # Create a new Stripe account
        new_account=  stripe.Account.create(
                type="standard",
                country="GB",
                email=email,
                business_profile={
                    "mcc": 5912,
                    "product_description": agency_name
                }
             )
        
       # Initiate Stripe Onboarding 
        account_link = stripe.AccountLink.create (
            account = new_account.id,
            refresh_url='https://your-domain.com/refresh',  # URL for Stripe updates
            return_url='https://your-domain.com/success',  # Redirect after onboarding 
            type='account_onboarding',
            collect='currently_due'  # Request financial data
        )

        rental_agency =  RentalAgencyProfile.objects.create(
            username = username,
            agencyname = agency_name,
            email = email,
            address = address,
            contact = contact,
            stripe_account_id=new_account.id     
       )

        rental_agency.stripe_account_link = account_link.url
        rental_agency.set_password(password)
        rental_agency.save()
        
          # Prepare the email content
        email_subject = "Welcome, Your Stripe Account Has Been Created"
        email_message = f"Hi {agency_name},\n\nWe are excited to inform you that your Stripe account has been created. Below are the details for your account:\n\nAccount ID: {new_account.id}\n\n" \
                        f"To complete the account onboarding, please follow this link: {account_link.url}\n\n" \
                        "Thank you for choosing our platform.\n\nBest Regards,\n RentSafe Team"

        # Define the email sender and recipient
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        # Send the email to the user
        send_mail(email_subject, email_message, email_from, recipient_list)

        messages.success(request, "Your account has been sucesfully created! Please check your mailBox for further instruction!")
        return redirect("signup")
    return render(request, "signup.html")



# Generate code for login of the user, resetting the password  of a user and send verification mail
def signin(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        
         # check the failed login attempts count
        user = RentalAgencyProfile.objects.filter(email=email).first()
        if user is not None:
                # check if the user is authenticated
                if user.check_password(password):
                  #  user.failed_login_attempts = 0
                   # user.save()
                    login(request, user)
                    request.session['user'] = str(user.id)
                    return redirect('listings')
                else:
                    if user.failed_login_attempts >=3:
                         messages.error(request, 'Your account has been locked due to 3 failed login attempts. Please reset your password.')
                         return redirect('reset_password')
                    else:
                         user.failed_login_attempts += 1
                         user.save()
                         messages.error(request,'Password incorrect. Please try again!')
        else:
                messages.error(request, 'User not found.')
            
    return render(request, "signin.html")

def reset_password(request):
     if request.method == "POST":
        email = request.POST["email"]
        user = RentalAgencyProfile.objects.filter(email=email).first()
    
        if user is not None:
            # generate a unique token for the user
            token = RentalAgencyProfile.objects.make_random_password()
            
            # store the token in the user's profile
            user.reset_password_token = token
            user.save()
            
            # send an email to the user with a link to generate a new password
            subject = "Reset Password"
            message = f"Please click the link below to reset your password: \n\n{request.scheme}://{request.get_host()}/reset-password-confirm/{token}/"
            email_from = settings.EMAIL_HOST_USER  
            to = [user.email, ] 
            print(to)
            send_mail(subject, message, email_from, to)  
        else:
            messages.error(request, 'The email address you entered does not exist in our system.')
            return redirect('reset_password')
     return render(request, "resetpass.html")

def reset_password_confirm(request, token):
    user = RentalAgencyProfile.objects.filter(reset_password_token=token).first()
    if user is not None:
        if request.method == "POST":
            password = request.POST["password"]
            if user.check_password(password):
                messages.error(request, "Please enter a new password.")
                return render(request, "resetpass_confirm.html", {"form": { "password": password}})
            user.set_password(password)
            user.reset_password_token = None
            user.save()
            messages.success(request, 'An email has been sent to your email address with instructions to reset your password.')
           # messages.success(request, "Your password has been reset. You can now sign in with your new password.")
            
            # Send email with login screen link
            subject = "Login Information"
            message = f"Hi {user.username},\n\nYour password has been reset. You can now sign in to our website using the following link:\n\n{request.scheme}://{request.get_host()}{reverse('signin')}\n\nThank you,\nThe Team"
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            send_mail(subject, message, email_from, recipient_list)
            if user is not None:
                login(request, user)
                return redirect("signin")
            else:
                messages.error(request, "The email address you entered does not exist in our system.")
                return render(request, "resetpass_confirm.html", {"form": {"password": ""}})
        else:
            return render(request, "resetpass_confirm.html", {"form": {"email": user.email, "password": ""}})
    else:
        messages.error(request, "The password reset link you followed is invalid or has expired.")
       # return redirect("signin")
    

def listings(request):
    property_details = PropertyDetail.objects.all()
    data = {
        'property_details': property_details
    }
    return render(request, "listings.html", data)

def add_property_detail(request, property_id):
    property = PropertyDetail.objects.get(id=property_id)
    if request.method == 'POST':
        form = PropertyDetailForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            form.save()
            return redirect('property_detail', property_id=property_id)
    else:
        form = PropertyDetailForm(instance=property)
    return render(request, 'add_detail.html', {'form': form, 'property': property})

def rental_agency_dashboard(request):
    blank_properties = PropertyDetail.objects.filter(rental_agency_id=None)
    context = {'blank_properties': blank_properties}
    return render(request, 'property_details.html', context)

def property_detail(request, property_id):
    property = PropertyDetail.objects.get(id=property_id)
    return render(request, 'property_details.html', {'property': property})

def make_claim(request):
    if request.method == 'POST':
        claim_data = {
            'ref_number': ''.join(str(random.randint(0, 9)) for _ in range(12)),
            'name': request.POST.get('name'),
            'contact': request.POST.get('contact'),
            'email': request.POST.get('email'),
            'address': request.POST.get('address'),
            'management_email': request.POST.get('management_email'),
            'cname': request.POST.get('cname'),
            'ccontact': request.POST.get('ccontact'),
            'cemail': request.POST.get('cemail'),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
            'quote_deatils':request.FILES.get('quote_deatils'),
            'statement_description': request.FILES.get('statement_description'),
            'pictures_description': request.FILES.get('pictures_description'),
            'damage_evidence': request.FILES.get('damage_evidence'),
            'police_report': request.FILES.get('police_report'),
        }
       # Create a new ClaimDetail instance with the form data
        new_entry = ClaimDetail.objects.create(**claim_data)

        # Send email with login screen link
        subject = "Claim Detail Information"
        message = f"Hi Your claim has been received. Here is your claim details:\n\nReference Number:{claim_data['ref_number']}\nName: {claim_data['name']}\nContact: {claim_data['contact']}\nEmail: {claim_data['cemail']}\nStart Date: {claim_data['start_date']}\nEnd Date: {claim_data['end_date']}\n\nThank you,\nThe Team"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [claim_data['email'], claim_data['cemail']]
        send_mail(subject, message, email_from, recipient_list)

        new_entry.save()  # Triggers reference number generation (as defined in the model)
        return redirect('listings')  # Redirect on success
    else:
       # context = {'transaction': transaction}  # Create proper context
        return render(request, 'claim.html') 

def fetch_claim_details(request):
    booking_ref_number = request.GET.get('booking_ref_number')
    if not booking_ref_number:
        return JsonResponse({'error': 'Booking reference number is required'}, status=400)
    try:
        transaction = Transaction.objects.get(booking_reference_number=booking_ref_number)
        # Fetch ClaimDetail directly using the transaction
        claim_detail = ClaimDetail.objects.get(cemail=transaction.client.email)
        data = {
            'name': claim_detail.name,
            'contact': claim_detail.contact, 
            'email': claim_detail.email,
            'address': claim_detail.address,
            'management_email': claim_detail.management_email,
            'cname': claim_detail.cname, 
            'ccontact': claim_detail.ccontact,
            'cemail': claim_detail.cemail,
            'start_date': claim_detail.start_date,
            'end_date': claim_detail.end_date
        }
        return JsonResponse(data)
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    except ClaimDetail.DoesNotExist:
        return JsonResponse({'error': 'Claim detail not found for this transaction'}, status=404) 


def dispute_resolution(request):
     if request.method == 'GET':
        active_claims = ClaimDetail.objects.filter(claim_status__in=[ClaimDetail.STATUS_CHOICES[0][0], ClaimDetail.STATUS_CHOICES[1][0]])

        for claim in active_claims:
            client_detail = ClientDetail.objects.get(email=claim.cemail)
            transaction = Transaction.objects.get(client=client_detail)
            claim_detail = ClaimDetail.objects.get(booking_transaction=transaction)
           
            if claim.booking_transaction:  # Check if a related transaction exists
                print("hI")
                booking_reference_number = claim.booking_transaction.booking_reference_number
            else:
                booking_reference_number = "No transaction associated"

        resolved_claims = ClaimDetail.objects.filter(claim_status=ClaimDetail.STATUS_CHOICES[2][0])

        context = {
            'active_claims': active_claims,
            'resolved_claims': resolved_claims
        }
        return render(request, 'dispute_resolution.html', context)
   
def download_documents(request,reference_number=None):
    if reference_number is None:
        reference_number = request.GET.get('reference_number')
        if not reference_number:
            return HttpResponseBadRequest('Missing required reference_number parameter.')
    documents = get_list_or_404(ClaimDetail, ref_number=reference_number)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for document in documents:
            if document.quote_deatils:
                file_name, file_ext = document.quote_deatils.name.rsplit('.', 1)
                zip_file.writestr(f"{document.name}-{file_name}.{file_ext}", document.quote_deatils.read(), compress_type=zipfile.ZIP_DEFLATED)
            if document.statement_description:
                file_name, file_ext = document.statement_description.name.rsplit('.', 1)
                zip_file.writestr(f"{document.name}-{file_name}.{file_ext}", document.statement_description.read(), compress_type=zipfile.ZIP_DEFLATED)
            if document.pictures_description:
                file_name, file_ext = document.pictures_description.name.rsplit('.', 1)
                zip_file.writestr(f"{document.name}-{file_name}.{file_ext}", document.pictures_description.read(), compress_type=zipfile.ZIP_DEFLATED)
            if document.damage_evidence:
                file_name, file_ext = document.damage_evidence.name.rsplit('.', 1)
                zip_file.writestr(f"{document.name}-{file_name}.{file_ext}", document.damage_evidence.read(), compress_type=zipfile.ZIP_DEFLATED)
            if document.police_report:
                file_name, file_ext = document.police_report.name.rsplit('.', 1)
                zip_file.writestr(f"{document.name}-{file_name}.{file_ext}", document.police_report.read(), compress_type=zipfile.ZIP_DEFLATED)
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{reference_number}-documents.zip"'
    return response


def check_claim_status(request,reference_number=None):
    if reference_number is None:
        reference_number = request.GET.get('reference_number')
        if not reference_number:
            return HttpResponseBadRequest('Missing required reference_number parameter.')
    claim = get_list_or_404(ClaimDetail, ref_number=reference_number)
    data = {
        'opened': claim[0].claim_status == ClaimDetail.STATUS_CHOICES[0][0],
        'reviewed': claim[0].claim_status == ClaimDetail.STATUS_CHOICES[1][0],
        'resolved': claim[0].claim_status == ClaimDetail.STATUS_CHOICES[2][0],
    }
    return JsonResponse(data)

def archive_resolved_disputes(request):
    archive_resolved_claims = ClaimDetail.objects.filter(claim_status='AR')
    return render(request, 'archive_resolved_disputes.html', {'archive_resolved_claims': archive_resolved_claims})

@csrf_exempt
def archive_dispute(request, reference_number=None):
    if reference_number is None:
        reference_number = request.GET.get('reference_number')
        if not reference_number:
            return HttpResponseBadRequest('Missing required reference_number parameter.')
    claim = get_object_or_404(ClaimDetail, ref_number=reference_number, claim_status='RE')
    claim.claim_status = 'AR'  # Assuming 'AR' means archived
    claim.save()
    return JsonResponse({'status': 'success'})
    
def booking(request):
     if request.method == 'GET':
        active_property = PropertyDetail.objects.filter(property_status=PropertyDetail.STATUS_CHOICES[0][0])
        available_property = PropertyDetail.objects.filter(property_status=PropertyDetail.STATUS_CHOICES[1][0])
        context = {'active_property': active_property, 'available_property': available_property}
        return render(request, 'booking.html', context)


def checkout_view(request,agency_id, property_id):
    property_obj = get_object_or_404(PropertyDetail, id=property_id, rental_agency_id=agency_id)  # More concise
    agency_id = property_obj.rental_agency_id.pk

    context = {
            'property': property_obj,
            'rental_agency_id': agency_id,
        }
    return render(request, "checkout.html", context)

# Payment Part
def create_stripe_account(agency_name, email):
    stripe._api_key = settings.STRIPE_SECRET_KEY
    new_account = stripe.Account.create(
            type="custom",
            country="GB",
            email=email,
            business_type="individual",
            business_profile={
                "mcc": 5912,
                "product_description": agency_name
            },
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
    return new_account

def register_rental_agency(request):
    if request.method == "POST":
        agency_name = request.POST.get('name')
        address = request.POST.get('address')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
    
        # Create a new Stripe account
        new_account=  stripe.Account.create(
                type="standard",
                country="GB",
                email=email,
                business_profile={
                    "mcc": 5912,
                    "product_description": agency_name
                }
             )
        
       # Initiate Stripe Onboarding 
        account_link = stripe.AccountLink.create (
            account = new_account.id,
            refresh_url='https://your-domain.com/refresh',  # URL for Stripe updates
            return_url='https://your-domain.com/success',  # Redirect after onboarding 
            type='account_onboarding',
            collect='currently_due'  # Request financial data
        )

        rental_agency =  RentalAgency.objects.create(
            name=agency_name,
            address=address,
            email=email,
            contact=contact, 
            stripe_account_id=new_account.id
       )

        rental_agency.stripe_account_link = account_link.url
        rental_agency.save()

        # Prepare the email content
        email_subject = "Welcome, Your Stripe Account Has Been Created"
        email_message = f"Hi {agency_name},\n\nWe are excited to inform you that your Stripe account has been created. Below are the details for your account:\n\nAccount ID: {new_account.id}\n\n" \
                        f"To complete the account onboarding, please follow this link: {account_link.url}\n\n" \
                        "Thank you for choosing our platform.\n\nBest Regards,\n RentSafe Team"

        # Define the email sender and recipient
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        # Send the email to the user
        send_mail(email_subject, email_message, email_from, recipient_list)
        messages.success(request, 'Please check your mailBox for further instruction!')
        return redirect('register_rental_agency')
    else:
        return render(request, "register_rental_agency.html")
       


def payment_complete(request, unique_rental_agency_id):
   # rental_agency = RentalAgency.objects.get(pk=unique_rental_agency_id)
    rental_agency = RentalAgency.objects.get(unique_id=unique_rental_agency_id)

    # Exchange authorization code from Stripe for an access token
    resp = stripe.OAuth.token(
        grant_type='authorization_code',
        code=request.GET['code'],  # Get this from the query parameters 
    )

    rental_agency.stripe_account_id = resp['stripe_user_id']
    rental_agency.save()

    return redirect('onboarding_success') 


def payment_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        evidence_proof = request.POST.get('evidence')
        deposit = request.POST.get('deposit')
        total = request.POST.get('amount')
 
        rental_agency_id = request.POST.get('rental_agency_id')
        property_id = request.POST.get('property_id')
   
        rental_agency = RentalAgency.objects.get(pk=rental_agency_id)
        property_instance = PropertyDetail.objects.get(pk=property_id)  
      
        # Create a Client object 
        client = ClientDetail.objects.create(
            name=name,
            email=email,
            contact = contact,
            evidence_proof = evidence_proof
        )
        
        card_name = request.POST.get('card_name')
        card_number = request.POST.get('card_number')
        card_expiry_month = request.POST.get('card_month')
        card_expiry_year = request.POST.get('card_year')
        card_cvc = request.POST.get('card_cvc')
        
        deposit_amount = int(deposit)  # Charge customer total + deposit
        rental_amount = int(total) - int(deposit)  # Amount to be sent to the rental agency

        try:
            # Step 1: Charge Deposit to RentSafe Platform
            stripe.Charge.create(
                amount= deposit_amount * 100,  
                currency="GBP",
                source="tok_visa"  # Replace with actual token
               # receipt_email=email,  # Assuming you want to send a receipt to the customer 
            )

            # Step 2: Charge Rental Amount (and optionally transfer)
            charge = stripe.Charge.create(
                amount = int(total) * 100,
                currency="GBP",
                source="tok_visa", 
                receipt_email=email, 
                on_behalf_of=rental_agency.stripe_account_id, 
                    transfer_data={ 
                    'destination': rental_agency.stripe_account_id,
                    'amount': rental_amount * 100 
                }
            )

            # Create Transaction 
            Transaction.objects.create(
                client=client,
                rental_agency_id=rental_agency,
                property_id=property_instance, 
                total_amount=total,
                deposit_amount = deposit,
                rental_amount = rental_amount,
                status='Completed', 
                stripe_charge_id=charge.id
            )
            
             # Prepare the email content
            email_subject = "Booking Confirmation"
            email_message = f"Hi {name},\n\nWe are excited to inform you that your booking has been succesful! Thank you for choosing our platform.\n\nBest Regards,\n RentSafe Team"
            # Define the email sender and recipient
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email, rental_agency.email]
            # Send the email to the user
            send_mail(email_subject, email_message, email_from, recipient_list)
            return render(request, 'payment_sucess.html')
        except stripe.error.StripeError as e:
            return render(request, 'payment_error.html', {'message': e.user_message})
    else:  
        # Code for GET requests (displaying the form)
        context = {
            'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY
        }
        return render(request, 'checkout.html', context)

def create_payment_link(request):
    if request.method == 'POST':
        booking_reference_number = ''.join(str(random.randint(0, 9)) for _ in range(12))
        cname = request.POST.get('cname')
        cemail = request.POST.get('cemail')
        contact = request.POST.get('contact')
        evidence = request.POST.get('evidence')

        deposit = request.POST.get('deposit')
        rental = request.POST.get('amount')
        total_amount = request.POST.get('total')
         

        property_id = request.POST.get('property_id')
        property_instance = PropertyDetail.objects.get(pk=property_id)  

        client = ClientDetail.objects.create(
            name=cname,
            email=cemail,
            contact = contact,
            evidence_proof = evidence
        )

        deposit_amount = int(deposit)  # Charge customer total + deposit
        rental_amount = int(rental)  # Amount to be sent to the rental agency

        # Create Stripe Payment Link (replace with your actual price ID)
        session = stripe.checkout.Session.create(
            line_items=[
                # First Product: Rental Property
                { 
                    'price_data': {
                        'currency': 'GBP',
                        'unit_amount': rental_amount * 100, 
                        'product_data': {
                            'name': 'Rental Property'
                        }
                    },
                    'quantity': 1
                },
                # Second Product: RentaSafe Deposit
                {
                    'price_data': {
                        'currency': 'GBP',
                        'unit_amount': deposit_amount * 100, 
                        'product_data': {
                            'name': 'RentaSafe Deposit' 
                        }
                    },
                    'quantity': 1  
                } 
            ],
            mode='payment',
            success_url="http://127.0.0.1:8000/payment_sucess", 
            cancel_url="http://127.0.0.1:8000/payment_error", 
            metadata = { 
                "property_id": property_id,
                "deposit_amount": deposit_amount,
                "rental_amount": rental_amount
            } 
        )  

        # Create Transaction 
        Transaction.objects.create(
            booking_reference_number = booking_reference_number,
            client=client,
            property_id=property_instance, 
            deposit_amount = deposit_amount,
            rental_amount = rental_amount,
            total_amount=total_amount,
            status='Completed', 
            stripe_charge_id=session.id
        )
        
         # Send email
        subject = 'Your Booking Property'
        message = f'Here is your booking refrance number: {booking_reference_number}' "\nThank you for choosing our platform.\n\nBest Regards,\n RentSafe Team"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [property_instance.rental_agency_id.email]
        # Send the email to the user
        send_mail(subject, message, email_from, recipient_list)

        # Send email
        subject = 'Your Payment Link'
        message = f'Here is your payment link: {session.url}' "\nThank you for choosing our platform.\n\nBest Regards,\n RentSafe Team"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [cemail]
        # Send the email to the user
        send_mail(subject, message, email_from, recipient_list)
        return render(request, "payment_sucess.html") # Redirect to a success page
    else:
        return render(request, "payment_error.html")  # Render a form 


def handle_payment_split(session):
    """Splits a payment between the platform and a connected rental agency."""
    property_id = session.metadata.get('property_id')
    if not property_id:
        print('Error: Missing property ID')
        return

    try:
        property_instance = PropertyDetail.objects.get(pk=property_id)
    except ObjectDoesNotExist:
        # Handle the case where the property is not found
        print(f'Error: Property with ID {property_id} does not exist')
        return
    
    deposit_amount = session.metadata.get('deposit_amount')
    rental_amount = session.metadata.get('rental_amount')

    print(property_id)
    print(deposit_amount)
    print(rental_amount)

    if not deposit_amount or not rental_amount:
        # Handle cases where metadata is missing
        print('Error: Missing deposit or total amount in metadata')
        return

    try:
        # Transfer using Stripe Connect (ensure rental agency is connected)
        stripe.Transfer.create(
            amount= int(rental_amount) * 100,  # Convert to cents
            currency='GBP',
            destination=property_instance.rental_agency_id.stripe_account_id,
        )
        
        # Authorize deposit amount using PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(deposit_amount) * 100,
            currency="GBP",
            customer=session.customer,
            capture_method="manual", # For holding the deposit
            metadata={
                'hold_until': (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
            }
        )

        # Update Transaction model 
        payment, created = Payment.objects.get_or_create(
            payment_reference_number=session.metadata.get('booking_reference_number'),
            defaults={
                'deposit_amount': deposit_amount,
                'rental_amount': rental_amount,  
                'total_amount': rental_amount + deposit_amount,
                'status': 'Initiated', 
                'payment_intent_id': payment_intent.id
            }
        )

        if not created:
            # Existing transaction; you might update status here if needed
            payment.payment_intent_id = payment_intent.id
            payment.save()

    except stripe.error.StripeError as e:
        # Handle specific Stripe errors (log, retry, notify)
        print(f'Stripe Error: {e}')
        # ... implement specific actions based on error type ...
        
@csrf_exempt  # Assuming Django
def handle_webhook(request):
    print("Webhook received!") 
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    print('Webhook ebvent')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        handle_payment_split(session)  # Function to implement below
   
    elif event.type == 'payment_intent.succeeded':
        intent = event.data.object
        transaction = Payment.objects.get(payment_intent_id=intent.id)
        transaction.status = 'Completed'
        transaction.save()
        print('payment intent')
    return HttpResponse(status=200)
        
def payment(request):
    return render(request, "payment.html")

def update_profile(request):
    if request.method == 'POST':
        print(request.user.is_authenticated)
        print("User ID:", request.user.id) 
        print("User Type:", type(request.user))  # Verify it's RentalAgencyProfile
        print("User has RentalAgencyProfile:", hasattr(request.user, 'rentalagencyprofile')) # Assuming a OneToOne or ForeignKey relation

        rental_agency_profile = getattr(request.user, 'rentalagencyprofile', None)  # Safely try to get the profile
        print("rental_agency_profile:", rental_agency_profile) 
        rentalAgency_profile = get_object_or_404(RentalAgencyProfile, pk=request.user.pk)
        rentalAgency_profile.username = request.POST.get('username') 
        rentalAgency_profile.agencyname = request.POST.get('agencyname') 
        rentalAgency_profile.email = request.POST.get('agencyemail')
        rentalAgency_profile.url = request.POST.get('url')
        rentalAgency_profile.address = request.POST.get('location')
        rentalAgency_profile.save()
        return render(request, 'my_account.html')  # Redirect to profile after update
    else:  # GET request
        rentalAgency_profile = get_object_or_404(RentalAgencyProfile, pk=request.user.pk)
        context = {
            'username': rentalAgency_profile.username,
            'agencyname': rentalAgency_profile.agencyname,
            'email': rentalAgency_profile.email,
            'url': rentalAgency_profile.url,
            'address': rentalAgency_profile.address
        }
        return render(request, 'my_account.html', context)
    
def my_account(request):
    return render(request, 'my_account.html')


def support(request):
    return render(request, 'support.html')


def index(request):
    return render(request, "index.html")

def signout(request):
    logout(request)
    return redirect('signin')
