from django.shortcuts import render, redirect
from django.views import View


class HomeView(View):
    def get(self, request):
        if self.request.user.is_authenticated:
            return redirect('overview')

        else:
            return render(request, 'home.html')
