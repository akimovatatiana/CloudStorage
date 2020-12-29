from django.utils.decorators import method_decorator
from django.views import View

from .forms import *

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

from subscriptions.models import SubscriptionPlan
from subscriptions import views as sub_views

from ..storage.utils import get_user_subscription


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


class ProfileView(View):
    @method_decorator(login_required())
    def get(self, request):
        context = self._get_subscription_data(request)

        form = UserUpdateForm(instance=request.user)

        context['form'] = form

        return render(request, 'profile/profile.html', context)

    @method_decorator(login_required())
    def post(self, request):
        context = self._get_subscription_data(request)

        form = UserUpdateForm(request.POST, instance=request.user)

        context['form'] = form

        if form.is_valid():
            form.save()

            return redirect('profile')

        return render(request, 'profile/profile.html', context)

    def _get_subscription_data(self, request):
        user_subscription = get_user_subscription(self.request)
        user_plan = None
        subscription_id = None

        if user_subscription:
            user_plan = user_subscription[0].subscription.plan
            subscription_id = user_subscription[0].pk

        return {'plan': user_plan, 'subscription_id': subscription_id}


class ChangePasswordView(View):
    @method_decorator(login_required())
    def get(self, request):
        form = PasswordChangeForm(user=request.user)

        return render(request, 'profile/change-password.html', {'form': form})

    @method_decorator(login_required())
    def post(self, request):
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()

            update_session_auth_hash(request, form.user)

            return redirect('profile')

        return render(self.request, 'profile/change-password.html', {'form': form})
