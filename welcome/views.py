from django.shortcuts import render
# from django.http import HttpResponse


def index(request):
    return render(request, 'welcome/index.html')
    # age = request.GET.get("age", 0)
    # name = request.GET.get("name", "Undefined")
    # return HttpResponse(f"<h2>Имя: {name}  Возраст: {age}</h2>")


def skills(request):
    return render(request, 'welcome/skills.html')


def tools(request):
    return render(request, 'welcome/tools.html')
