from functools import update_wrapper

from django.utils.decorators import classonlymethod

from .forms import *

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.shortcuts import get_object_or_404

from subscriptions.models import UserSubscription
from subscriptions import views as sub_views
from subscriptions import forms as sub_forms


def get_user(request, pk):
    user = User.objects.get(pk=pk)
    user_subscription = UserSubscription.objects.get_queryset()

    if user_subscription.filter(user=user):
        user_plan = user_subscription.filter(user=user)[0].subscription.plan
    else:
        user_plan = None

    context = {
        "user": user,
        "plan": user_plan
    }

    return render(request, "profile/profile.html", context)


def get_all_users(request):
    keys = User.objects.count() + 1
    users = []

    # Traverse all users by primary keys
    for pk in range(1, keys):
        user = User.objects.get(pk=pk)
        users.append(user)

    context = {
        "users": users
    }

    return render(request, "profile/users.html", context)


@login_required
def redirect_user(request):
    return get_user(request, pk=request.user.pk)


def signup(request):
    plan_id = request.POST.get('plan_id', '')
    redirect_from = request.POST.get('redirect_from', '')

    if request.method == 'POST' and plan_id != '' and redirect_from == 'signup':
        form = UserSignUpForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            login(request, user)

            return sub_views.SubscribeView.as_view()(request)
    else:
        form = UserSignUpForm()

    return render(request, 'registration/signup.html', {'form': form, 'plan_id': plan_id})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST)

        if form.is_valid():
            form = UserUpdateForm(request.POST, instance=request.user)
            form.save()

            return redirect('profile')

        # else:
        #     form = UserUpdateForm(instance=request.user)

            # return render(valid_request, 'profile/profile.html', {'form': form})

    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'profile/profile.html', {'form': form})
