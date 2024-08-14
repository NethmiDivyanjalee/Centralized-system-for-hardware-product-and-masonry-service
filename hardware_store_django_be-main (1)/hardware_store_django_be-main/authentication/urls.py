from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path("auth/health/", views.health_check, name="health"),
    path("signup/<str:role>", views.signup, name="signup"),
    path("login/", obtain_auth_token, name="login"),
    path("account/logout/", views.logout, name="logout"),
    path("account/", views.account, name="account"),


]
