"""
URL configuration for project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views
from finances import views as finance_views
from goals import views as goal_views
from dashboard import views as dashboard_views


urlpatterns = [
    path('', dashboard_views.root_redirect, name='root'),
    path('', include('dashboard.urls')),
    path('auth/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('finances/', include('finances.urls')),
    path('goals/', include('goals.urls')),

    # ===== Compatibility API routes (used by static/Spendo.js) =====
    path('api/signup/', account_views.signup_view, name='api_signup'),
    path('api/login/', account_views.login_view, name='api_login'),
    path('api/dashboard/', finance_views.dashboard_data, name='api_dashboard_data'),
    path('api/categories/add/', finance_views.add_category, name='api_add_category'),
    path('api/budgets/set/', finance_views.set_budget, name='api_set_budget'),
    path('api/transactions/add/', finance_views.add_transaction, name='api_add_transaction'),
    path('api/transactions/update/<int:transaction_id>/', finance_views.update_transaction, name='api_update_transaction'),
    path('api/transactions/delete/<int:transaction_id>/', finance_views.delete_transaction, name='api_delete_transaction'),
    path('api/goals/deposit/', goal_views.depositGoalAmount, name='api_goals_deposit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
