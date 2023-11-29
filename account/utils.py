from account.models import User, UserProfile

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