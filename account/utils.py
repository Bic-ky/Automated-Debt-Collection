from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, UserProfile

def detectUser(user):
    if user.role == User.ADMIN:
            redirectUrl = 'account:admindashboard'
    elif user.role == User.USER:
        redirectUrl = 'account:userdashboard'
               
    elif user.role == None and user.is_superuser:
        redirectUrl = '/admin'
        return redirectUrl
    else:
        redirectUrl = None
    
    return redirectUrl

def send_verification_email(request, user, mail_subject, email_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    user_profile = UserProfile.objects.get(user=user)
    message = render_to_string(email_template, {
        'user': user_profile,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user_profile.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()
