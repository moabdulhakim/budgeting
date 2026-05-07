from django.db.models import Sum
from .models import Transaction, Budget, Notification
from django.db.models.signals import post_save
from django.dispatch import receiver



@receiver(post_save, sender=Transaction)
def checkBudgetAmount(sender, instance, created, **kwargs):
    if created and instance.type == "expense":
        budget = Budget.objects.filter(user=instance.user, category=instance.category).first()
        
        if budget:
            spent_data = Transaction.objects.filter(
                user=instance.user, 
                category=instance.category,
                type="expense",
                date__date__gte=budget.start_date,
                date__date__lte=budget.end_date
            ).aggregate(total_spent=Sum('amount'))

            total_spent = spent_data['total_spent'] or 0

            spending_percentage = (total_spent/budget.amount) *100

            if spending_percentage >= budget.alert_threshold:
                if spending_percentage <= 1:
                    notification_msg = f"Budget Alert — {budget.category.name}: You've used {spending_percentage:.0f}% of your {budget.category.name} budget."
                else:
                    notification_msg = f"Budget Exceeded — {budget.category.name}! You've exceeded your ${budget.amount} budget by ${total_spent-budget.amount}."
                Notification.objects.create(
                    user=instance.user,
                    message=notification_msg
                )
            
