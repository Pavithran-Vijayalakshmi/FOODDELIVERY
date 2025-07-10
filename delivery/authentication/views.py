from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    return redirect('restaurants:List Of Restaurants')

def LoginView(request):
    if(request.method == "POST"):
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("authentication:login")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form':form})