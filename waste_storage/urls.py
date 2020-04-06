"""waste_storage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from waste.views import home_view, log_in, log_out

urlpatterns = [
    path('', home_view, name='home'),
    path('log_out_submit', log_out),
    path('log_in_submit', log_in),
    path('admin/', admin.site.urls),
    path('waste/', include('waste.urls')),
    path('add/', include('waste.urls'))
]
