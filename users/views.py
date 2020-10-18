from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django import forms

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )

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

@login_required
def redirect_user(request):
    return get_user(request, pk=request.user.pk)


def get_user(request, pk):
    user_obj = User.objects.get(pk=pk)

    context = {
        "user": user_obj
    }

    return render(request, "profile/profile.html", context)


def get_all_users(request):
    keys = User.objects.count() + 1
    print(keys)
    users_obj = []

    # Traverse all users by primary keys
    for pk in range(1, keys):
        user_obj = User.objects.get(pk=pk)
        users_obj.append(user_obj)

    context = {
        "users": users_obj
    }

    return render(request, "profile/users.html", context)
