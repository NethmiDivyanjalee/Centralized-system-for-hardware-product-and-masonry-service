from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path("populate/", views.populate, name="populate"),


]
