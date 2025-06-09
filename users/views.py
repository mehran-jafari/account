from django.http import HttpResponse

def user_home(request):
    return HttpResponse("User Home")
