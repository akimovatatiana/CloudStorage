from .forms import *

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


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
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('profile')
    else:
        form = UserSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
