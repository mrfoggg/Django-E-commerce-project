from django.shortcuts import render

from products.models import Category


# Create your views here.
def index(request):
    categories = Category.objects.filter(is_active=True, mptt_level=0).only('name', 'mptt_level', 'parent')
    return render(
        request,
        'home/index.html',
        context={'categories': categories, 'title': "Главная страница", }
    )