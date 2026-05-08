import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User

# استدعاء الموديلز (افترضت إن اسم الـ app هو finances زي ما اتفقنا)
from finances.models import Category, Budget, Transaction, Notification

print("Starting to plant seeds... 🌱")

# 1. البحث عن اليوزر اللي اسمه Mohammad أو إنشاؤه
user = User.objects.filter(first_name="Mohammad").first()

if not user:
    print("User 'Mohammad' not found! Creating a new user...")
    # هيعمل يوزر جديد كاحتياطي عشان الكود يكمل
    user = User.objects.create_user(username="mohakim_test", first_name="Mohammad", password="password123")

print(f"Seeding data for user: {user.first_name} (ID: {user.id})")

# 2. تنظيف الداتا القديمة لليوزر ده (عشان لو رنيت الكود كذا مرة)
Transaction.objects.filter(user=user).delete()
Budget.objects.filter(user=user).delete()
Category.objects.filter(user=user, is_custom=True).delete()
Notification.objects.filter(user=user).delete()

# 3. إنشاء الأقسام (Categories)
categories_data = [
    {'name': 'Salary', 'type': 'income', 'icon': '💰'},
    {'name': 'Freelance', 'type': 'income', 'icon': '💻'},
    {'name': 'Food & Dining', 'type': 'expense', 'icon': '🍔'},
    {'name': 'Transportation', 'type': 'expense', 'icon': '🚗'},
    {'name': 'Utilities', 'type': 'expense', 'icon': '⚡'},
    {'name': 'Entertainment', 'type': 'expense', 'icon': '🎬'},
]

category_objs = {}
for data in categories_data:
    # إنشاء الـ Category بناءً على موديل فاطمة
    cat = Category.objects.create(user=user, name=data['name'], icon=data['icon'], is_custom=True)
    category_objs[data['name']] = {'obj': cat, 'type': data['type']}

# 4. إنشاء 150 معاملة (Transactions) موزعة على آخر 6 شهور
now = timezone.now()
transaction_names = {
    'Food & Dining': ['Groceries from Carrefour', 'Dinner with friends', 'Morning Coffee', 'Snacks'],
    'Transportation': ['Uber ride', 'Gas Station', 'Metro Tickets'],
    'Utilities': ['Electricity Bill', 'Internet Subscription', 'Water Bill'],
    'Entertainment': ['Cinema Ticket', 'Netflix Subscription', 'Video Game'],
    'Salary': ['Monthly Salary'],
    'Freelance': ['Upwork Client', 'Website Design Project']
}

for _ in range(150):
    random_days = random.randint(0, 180)
    random_date = now - timedelta(days=random_days)
    
    # اختيار قسم عشوائي
    cat_name = random.choice(list(category_objs.keys()))
    cat_info = category_objs[cat_name]
    
    # تحديد المبلغ بناءً على النوع (الدخل أكبر من المصاريف)
    if cat_info['type'] == 'income':
        amount = random.uniform(3000.0, 15000.0)
    else:
        amount = random.uniform(50.0, 1500.0)
        
    Transaction.objects.create(
        user=user,
        category=cat_info['obj'],
        name=random.choice(transaction_names[cat_name]),
        amount=round(amount, 2),
        type=cat_info['type'],
        date=random_date,
        payment_method=random.choice(['Cash', 'Credit Card', 'InstaPay']),
        description="Auto-generated seed transaction"
    )

# 5. إنشاء ميزانيات (Budgets) للشهر الحالي
start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
# حساب آخر يوم في الشهر
if now.month == 12:
    end_of_month = start_of_month.replace(year=now.year + 1, month=1) - timedelta(seconds=1)
else:
    end_of_month = start_of_month.replace(month=now.month + 1) - timedelta(seconds=1)

budget_cats = ['Food & Dining', 'Transportation', 'Entertainment']
for cat_name in budget_cats:
    Budget.objects.create(
        user=user,
        category=category_objs[cat_name]['obj'],
        amount=random.choice([2000.00, 3000.00, 5000.00]),
        start_date=start_of_month.date(),
        end_date=end_of_month.date(),
        alert_threshold=80
    )

# 6. إنشاء تنبيهات (Notifications)
Notification.objects.create(user=user, message="Welcome to your new Budget Dashboard, Mohammad!")
Notification.objects.create(user=user, message="Warning: You have used 85% of your Food & Dining budget this month.")

print("Done! 🌳 Database is fully seeded with realistic data. You can exit the shell now.")