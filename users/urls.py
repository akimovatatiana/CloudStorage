from django.contrib.auth import views
from django.urls import path

from .views import *

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', redirect_user, name="profile"),
    path('all/', get_all_users, name="all_users"),
    path('signup/', signup, name='signup'),
    path('signup-free/', signup, name='signup-free'),
    path('signup-basic/', signup, name='signup-basic'),
    path('signup-standard/', signup, name='signup-standard'),
    path('signup-premium/', signup, name='signup-premium')
]
