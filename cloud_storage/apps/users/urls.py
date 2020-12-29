from django.conf.urls import url
from django.contrib.auth import views

from .views import *

urlpatterns = [
    url('login/', views.LoginView.as_view(), name='login'),
    url('logout/', views.LogoutView.as_view(), name='logout'),
    url('profile/', ProfileView.as_view(), name="profile"),
    url('change-password/', ChangePasswordView.as_view(), name="change-password"),
    url('signup-basic/', SignUpView.as_view(), name='signup-basic'),
    url('signup-standard/', SignUpView.as_view(), name='signup-standard'),
    url('signup-premium/', SignUpView.as_view(), name='signup-premium'),
]
