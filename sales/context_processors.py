from .models import Action, Client
from datetime import date, timedelta


def action_counts(request):
    manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
    
    auto_count = Action.objects.filter(type='auto', completed=False).count()
    total_count = manual_not_completed_count + auto_count

    return {
        'manual_not_completed_count': manual_not_completed_count,
        'auto_count': auto_count,
        'total_count': total_count,
        
    }
    

def check_upcoming_actions(request, days_in_future=2):
    user = request.user

    # Check if the user is authenticated
    if user.is_authenticated:
        today = date.today()
        future_date = today + timedelta(days=days_in_future)

        # Filter actions for the current user where follow-up date is up to two days in the future
        upcoming_actions = Client.objects.filter(
            collector=user,
            action__followup_date__range=[today, future_date]
        ).distinct()

        # Count of upcoming actions
        upcoming_actions_count = upcoming_actions.count()

        # Fetch clients for the current user where follow-up date is today
        clients_with_follow_up_today = Client.objects.filter(
            collector=user,
            action__followup_date=today
        ).distinct()
        
        follow_up_today = clients_with_follow_up_today.count()

        return {
            'upcoming_actions': upcoming_actions,
            'upcoming_actions_count': upcoming_actions_count,
            'clients_with_follow_up_today': clients_with_follow_up_today,
            'follow_up_today': follow_up_today,
        }
    else:
        # If the user is not authenticated, return empty data
        return {
            'upcoming_actions': [],
            'upcoming_actions_count': 0,
            'clients_with_follow_up_today': [],
            'follow_up_today': 0,
        }

