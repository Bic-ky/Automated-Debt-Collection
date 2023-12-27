from .models import Action  # Update the import path based on your project structure

def action_counts(request):
    manual_not_completed_count = Action.objects.filter(type='manual', completed=False).count()
    auto_count = Action.objects.filter(type='auto', completed=False).count()
    total_count = manual_not_completed_count + auto_count

    return {
        'manual_not_completed_count': manual_not_completed_count,
        'auto_count': auto_count,
        'total_count': total_count,
    }
