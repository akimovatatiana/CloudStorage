from django.views import View

from .forms import *

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

from subscriptions.models import UserSubscription, SubscriptionPlan
from subscriptions import views as sub_views


class SignUpView(View):
    def get(self, request):
        form = UserSignUpForm()
        plan_id = request.POST.get('plan_id', '')

        return render(self.request, 'registration/signup.html', {'form': form, 'plan_id': plan_id})

    def post(self, request):
        plan_id = self.request.POST.get('plan_id', '')
        plan = SubscriptionPlan.objects.filter(pk=plan_id)

        redirect_from = self.request.POST.get('redirect_from', '')

        form = UserSignUpForm()

        if plan and redirect_from == 'signup':
            form = UserSignUpForm(self.request.POST)

            if form.is_valid():
                form.save()

                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)

                login(self.request, user)

                return sub_views.SubscribeView.as_view()(self.request)

        return render(self.request, 'registration/signup.html', {'form': form, 'plan_id': plan_id})


@login_required
def profile(request):
    user = User.objects.get(pk=request.user.pk)
    user_subscription = UserSubscription.objects.get_queryset().filter(user=user)

    if user_subscription:
        subscription = user_subscription[0]

        user_plan = subscription.subscription.plan

        user_subscription_id = subscription.pk

    else:
        user_plan = None

        user_subscription_id = None

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()

            return redirect('profile')

    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'profile/profile.html', {'form': form, 'plan': user_plan,
                                                    'subscription_id': user_subscription_id})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()

            update_session_auth_hash(request, form.user)

            return redirect('profile')

        else:
            return redirect('change-password')

    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'profile/change-password.html', {'form': form})
