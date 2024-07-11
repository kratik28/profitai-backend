"""
URL configuration for profitai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include
from user_profile import views as user_profile_view

urlpatterns = [
    path('admin/', admin.site.urls),    
    path("user_profile/",include("user_profile.urls")),
    path('invoice/',include('invoice.urls')),
    path('inventory/',include('inventory.urls')),
    path('master_menu/',include('master_menu.urls')),
    path('employee/',include('employee.urls')),
    path('expense/',include('expense.urls')),    
    path('online_store/',include('online_store.urls')),
    path('profit_and_loss/',include('profit_and_loss.urls')),
    path('request_invoices/',include('request_invoices.urls'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)