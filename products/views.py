from django.shortcuts import render, get_object_or_404
from django.views.generic.list import ListView
from products.models import Category, ProductInCategory


class CategoryView(ListView):
    template_name = "products/category.html"
    context_object_name = 'products_list'

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True).only('name', 'mptt_level', 'parent')
        self.categories = queryset.filter(mptt_level=0)
        self.category = get_object_or_404(queryset, slug=self.kwargs['category_slug'])
        return ProductInCategory.objects.filter(category=self.category).order_by('position_product').only(
            'product__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.categories
        context['category'] = context['title'] = self.category
        return context

# Create your views here.
