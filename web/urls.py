"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rentsafe import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signin', views.signin, name='signin'),
    path('signup', views.signup, name='signup'),
    path('register_rental_agency', views.register_rental_agency, name='register_rental_agency'),
    path('listings', views.listings, name='listings'),
    path('make_claim/', views.make_claim, name='make_claim'),
    path('fetch_claim_details/', views.fetch_claim_details, name='fetch_claim_details'), 
    path('dispute_resolution', views.dispute_resolution, name='dispute_resolution'),
    path('download_documents/<str:reference_number>/', views.download_documents, name='download_documents'),
    path('check_claim_status/<str:reference_number>/', views.check_claim_status, name='check_claim_status'),
    path('archive_resolved_disputes/', views.archive_resolved_disputes, name='archive_resolved_disputes'),
    path('archive_dispute/<str:reference_number>/', views.archive_dispute, name='archive_dispute'),
    path('property_detail/<int:property_id>/', views.property_detail, name='property_detail'),
    path('add-detail/<int:property_id>', views.add_property_detail, name='add-detail'),
    path('booking', views.booking, name='booking'),
    path('create_payment_link/', views.create_payment_link, name='create_payment_link'),
    path('stripe-webhook/', views.handle_webhook, name='stripe-webhook'),
    path('payment_view/', views.payment_view, name='payment_view'),
    path('reset_password', views.reset_password, name='reset_password'),
    path("reset-password-confirm/<str:token>/", views.reset_password_confirm, name="reset_password_confirm"),
    path('account', views.my_account, name='my_account'),
    path('update_profile', views.update_profile, name='update_profile'),
    path('support', views.support, name='support'),
    path('signout', views.signout, name='signout'),

   # path('', include('rentsafe.urls')),
   # path('generate_new_password/<str:token>', views.generate_new_password, name='generate_new_password'),
    path('index', views.index, name='index'),
    #path('reset_password/', PasswordResetView.as_view(), name="reset_password"),
    path('admin/', admin.site.urls),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



