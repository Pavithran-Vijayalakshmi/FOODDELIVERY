from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def LoginView(request):
    if(request.method == "POST"):
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("authentication:login")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form':form})