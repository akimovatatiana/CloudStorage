from django.http import HttpRequest, HttpResponse
from django.http import QueryDict

from .forms import *

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse


import requests

from subscriptions import views as sub_views


def get_user(request, pk):
    user_obj = User.objects.get(pk=pk)

    context = {
        "user": user_obj
    }

    return render(request, "profile/profile.html", context)


def get_all_users(request):
    keys = User.objects.count() + 1
    users_obj = []

    # Traverse all users by primary keys
    for pk in range(1, keys):
        user_obj = User.objects.get(pk=pk)
        users_obj.append(user_obj)

    context = {
        "users": users_obj
    }

    return render(request, "profile/users.html", context)


@login_required
def redirect_user(request):
    return get_user(request, pk=request.user.pk)


def signup(request):
    plan_id = request.POST.get('plan_id', '')
    redirect_from = request.POST.get('redirect_from', '')
    print(redirect_from)
    if request.method == 'POST' and plan_id != '' and redirect_from == 'signup':
        form = UserSignUpForm(request.POST)
        print(redirect_from)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)

            # redirect('signup-free-payment')

    else:
        form = UserSignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


def payment(request):
    pass
