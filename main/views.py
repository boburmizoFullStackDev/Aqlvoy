from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def student_page(request):
    return render(request, 'student.html')


def teacher_page(request):
    return render(request, 'teacher.html')


def parent_page(request):
    return render(request, 'parent.html')
