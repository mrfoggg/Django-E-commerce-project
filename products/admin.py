import copy

import nested_admin
from django.db.models import Subquery, OuterRef, JSONField
from django.contrib import admin
from django.http import HttpResponseRedirect
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter

from .admin_form import *
from django.contrib.postgres.aggregates import ArrayAgg


class ProductImageInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # fields = ['position', ('image_image', 'image', 'name', 'is_main_1', 'is_main_2', 'is_active')]
    fields = ['position', ('image', 'name', 'is_main_1', 'is_main_2', 'is_active')]
    model = ProductImage
    sortable_field_name = "position"
    extra = 0


class BrandInLine(admin.TabularInline):
    model = Brand
    extra = 0


class CategoryForProductInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    formset = CategoryForProductInLineFormSet
    fields = ('position_category', 'category', 'self_attribute_group')
    readonly_fields = ('self_attribute_group',)
    model = ProductInCategory
    sortable_field_name = 'position_category'
    ordering = ('position_category',)
    # classes = ['collapse']
    extra = 0


class ProductInCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position_product', 'product', 'get_product_category_link')
    readonly_fields = ('product', 'get_product_category_link')
    model = ProductInCategory
    sortable_field_name = "position_product"
    ordering = ('position_product',)
    # classes = ['collapse']
    extra = 0
    verbose_name_plural = 'Порядок товаров в категории'
    verbose_name = 'Товар'
    can_delete = False


class AttrGroupInCategoryInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # class AttrGroupInCategoryInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    fields = (('position', 'group', 'self_attributes_links',),)
    readonly_fields = ('self_attributes_links',)
    model = AttrGroupInCategory
    sortable_field_name = "position"
    autocomplete_fields = ('group',)
    # classes = ['collapse']
    extra = 0


class CategoriesInGroupInline(nested_admin.NestedTabularInline):
    fields = ('position', 'category',)
    model = AttrGroupInCategory
    formset = CategoriesInGroupInlineFormSet
    ordering = ('category',)
    extra = 0
    verbose_name = "Категория товаров содержащая текущую группу атрибутов"
    verbose_name_plural = "Категории товаров содержащие текущую группу атрибутов"


class AttributesInGroupInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'attribute', 'type_of_value', 'self_value_variants')
    readonly_fields = ('type_of_value', 'self_value_variants',)
    model = AttributesInGroup
    sortable_field_name = "position"
    extra = 0
    autocomplete_fields = ('attribute',)
    form = AttributeForm


class ItemOfCustomOrderGroupInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'category', 'getlink_group', 'self_attributes_links',)
    readonly_fields = ('category', 'self_attributes_links', 'getlink_group',)
    model = ItemOfCustomOrderGroup
    formset = ItemOfCustomOrderGroupInLineFormSet
    sortable_field_name = "position"
    ordering = ('position',)
    extra = 0
    # can_delete = False

    # def has_add_permission(self, request, obj=None):
    #     return False


class ShotParametersOfProductInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'attribute', 'name', 'is_active')
    extra = 0
    model = ShotParametersOfProduct
    sortable_field_name = "position"

    # classes = ['collapse']
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = AttributesInGroup.objects.filter(group__in=request._obj_).order_by('group')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MiniParametersOfProductInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'attribute', 'name', 'is_active')
    extra = 0
    model = MiniParametersOfProduct
    sortable_field_name = "position"

    # classes = ['collapse']
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = AttributesInGroup.objects.filter(group__in=request._obj_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PricesOtherShopInline(nested_admin.NestedTabularInline):
    model = PricesOtherShop
    fields = ('created', 'shop', 'price', 'updated', 'url', 'info')
    readonly_fields = ('created', 'updated',)
    extra = 0
    # sortable_field_name = "updated"


@admin.register(Category)
class CategoryModelAdmin(nested_admin.NestedModelAdmin, SummernoteModelAdmin, DraggableMPTTAdmin, ):
    fieldsets = (
        (
            'Основное', {
                'fields': (
                    ('name', 'parent'),
                    ('slug', 'id', 'is_active'),
                    ('created', 'updated'),
                ),
                'classes': ('tab-fs-none',)
            }
        ),
        (
            'Изображения', {
                'fields': (
                    'image', 'sign'
                ),
                'classes': ('tab-fs-none',)
            }
        ),
        (
            'Описание', {
                'fields': (
                    'description',
                ),
                'classes': (
                    'order-1',
                    'baton-tabs-init',
                    'baton-tab-inline-related_groups',
                    'baton-tab-inline-related_shot_attributes',
                    'baton-tab-inline-related_mini_attributes',
                    'baton-tab-inline-related_products',
                )
            }
        )
    )
    list_display = ('tree_actions', 'indented_title', 'self_attribute_group',)
    model = Category
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('id', 'created', 'updated', 'image_view', 'sign_view', 'self_attribute_group',)
    inlines = (
        ShotParametersOfProductInline, MiniParametersOfProductInline, AttrGroupInCategoryInline,
        ProductInCategoryInLine)

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            request._obj_ = list(map(lambda x: x.group_id, obj.related_groups.all()))
            # request._rel_shot_ = list(map(lambda x: x.attribute.attribute, obj.related_shot_attributes.all()))
            # request._rel_mini_ = list(map(lambda x: x.attribute.attribute, obj.related_mini_attributes.all()))
        else:
            request._obj_ = []
            # request._rel_shot_ = []
            # request._rel_mini_ = []
        return super(CategoryModelAdmin, self).get_form(request, obj, **kwargs)

    @staticmethod
    def image_view(obj):
        return mark_safe('<img src="{url}" width=95 height=95/>'.format(url=obj.image.url))

    @staticmethod
    def sign_view(obj):
        return mark_safe('<img src="{url}" width=40 height=40/>'.format(url=obj.sign.url))

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(s_attribute_group=ArrayAgg('related_groups__group__name'))

    @staticmethod
    def self_attribute_group(obj):
        return obj.s_attribute_group


def save_and_make_copy(objct, model_to_copy):
    objct.save()
    objct_copy = copy.copy(objct)
    objct_copy.id = None
    objct_copy.slug = None
    copies = [0]
    for atr in model_to_copy.objects.filter(name__startswith=objct.name + ' (@копия #'):
        left_part_name = atr.name[(atr.name.find(' (@копия #') + 10):]
        number_of_copy = int(left_part_name[:left_part_name.find(')')])
        copies.append(number_of_copy)
    objct_copy.name = objct.name + ' (@копия #%s)' % (max(copies) + 1)
    return objct_copy


@admin.register(Product)
class ProductModelAdmin(nested_admin.NestedModelAdmin, SummernoteModelAdmin):
    form = ProductForm
    model = Product
    summernote_fields = ('description',)
    list_display = ('art', 'name', 'rating', 'get_product_category_link', 'is_active')
    list_display_links = ('name',)
    list_editable = ("rating", 'is_active',)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        'created', 'updated', 'category_collection', 'get_category_collection_link', 'get_shot_parameters_admin_field',
        'get_mini_parameters_admin_field')
    list_filter = (('admin_category', TreeRelatedFieldListFilter), 'brand')
    inlines = (ProductImageInline, CategoryForProductInLine, PricesOtherShopInline)
    change_form_template = "products/product_changeform.html"
    fieldsets = (
        ("Основное", {
            'fields': (
                ('name', 'art',), ('slug', 'admin_category'),
                ('brand', 'is_active',),
                ('created', 'updated',),),
            'classes': ('tab-fs-none',),
        }),

        ("Габбариты и вес",
         {'fields': (('length', 'width', 'height',), ('length_box', 'width_box', 'height_box', 'weight')),
          'classes': ('tab-fs-none',),
          }),

        ("Разное", {
            'fields': (('warranty', 'url',),),
            'classes': ('tab-fs-none',),
        }),

        ("Характеристики", {
            # 'classes': ('collapse',),
            'fields': (
                ('parameters',), ('get_shot_parameters_admin_field', 'get_mini_parameters_admin_field'),
                ('description', 'parameters_structure'),
                ('is_active_custom_order_group', 'get_category_collection_link',)),
            'classes': (
                'order-0', 'baton-tabs-init', 'baton-tab-inline-related_categories', 'baton-tab-inline-productimage',
                'baton-tab-inline-pricesothershop',),
        }),

    )

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            product_copy = save_and_make_copy(obj, Product)
            product_copy.art = None
            product_copy.url = None
            product_copy.save()
            for cat in Category.objects.filter(related_products__product_id=obj.id):
                ProductInCategory.objects.create(product=product_copy, category=cat)
            for ph in obj.productimage_set.all():
                ProductImage.objects.create(product=product_copy, image=ph.image)
            return HttpResponseRedirect(reverse('admin:products_product_change', args=(product_copy.id,)))
        return super().response_change(request, obj)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    fields = ('name', 'slug', 'is_active')
    inlines = (BrandInLine,)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AttrGroup)
class AttrGroupAdmin(nested_admin.NestedModelAdmin):
    form = AttrGroupForm
    model = AttrGroup
    change_form_template = "products/group_attribute_changeform.html"
    fields = (('name', 'slug', 'is_active'), ('created', 'updated'))
    readonly_fields = ('created', 'updated', 'self_attributes_links',)
    list_display = ('name', 'self_attributes_links', 'is_active',)
    list_display_links = ('name',)
    inlines = (AttributesInGroupInline, CategoriesInGroupInline,)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            group_copy = save_and_make_copy(obj, AttrGroup)
            group_copy.save()
            for atr in Attribute.objects.filter(related_groups__group=obj):
                AttributesInGroup.objects.create(group=group_copy, attribute=atr)
            return HttpResponseRedirect(reverse('admin:products_attrgroup_change', args=(group_copy.id,)))
        return super().response_change(request, obj)


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    form = AttributeForm
    fields = (('name', 'slug'), ('type_of_value',), ('created', 'updated', 'is_active'), 'value_list',)
    filter_horizontal = ('value_list',)
    list_display = ('name', 'slug', 'type_of_value', 'self_value_variants', 'is_active')
    readonly_fields = ('self_value_variants', 'created', 'updated',)
    prepopulated_fields = {"slug": ("name",), }
    ordering = ('position',)
    search_fields = ['name']
    change_form_template = "products/attribute_changeform.html"

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            attribute_copy = save_and_make_copy(obj, Attribute)
            attribute_copy.save()
            return HttpResponseRedirect(reverse('admin:products_attribute_change', args=(attribute_copy.id,)))
        return super().response_change(request, obj)


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    model = AttributeValue
    fields = (('name', 'slug', 'is_active'), ('created', 'updated'))
    list_display = ('name', 'slug', 'is_active', 'created', 'updated',)
    readonly_fields = ('created', 'updated',)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CategoryCollection)
class CategoryCollectionAdmin(nested_admin.NestedModelAdmin):
    fields = ('id', 'category_list', ('is_active_custom_order_group', 'is_active_custom_order_shot_parameters',
                                      'is_active_custom_order_mini_parameters',),)
    readonly_fields = ('id',)
    model = CategoryCollection
    form = CategoryCollectionForm
    inlines = (ItemOfCustomOrderGroupInline,)


@admin.register(SomeSites)
class SomeSitesAdmin(nested_admin.NestedModelAdmin):
    model = SomeSites


admin.site.register(ProductImage)
admin.site.register(Brand)
