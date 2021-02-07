import copy

import nested_admin
from django.db.models import Subquery, OuterRef, JSONField
from django.contrib import admin
from django.http import HttpResponseRedirect

from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter

from .admin_form import *
from .models import *
from django.contrib.postgres.aggregates import ArrayAgg


class ProductImageInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ['position', ('image', 'name', 'is_main_1', 'is_main_2', 'is_active')]
    model = ProductImage
    sortable_field_name = "position"
    extra = 0


class BrandInLine(admin.TabularInline):
    model = Brand
    extra = 0


class CategoryForProductInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    formset = CategoryForProductInLineFormSet
    fields = ('position_category', 'category', 'self_attribute_groups')
    readonly_fields = ('self_attribute_groups',)
    model = ProductInCategory
    sortable_field_name = 'position_category'
    ordering = ('position_category',)
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            s_attribute_group_names_list=ArrayAgg('category__related_groups__group__name'),
            s_attribute_group_id_list=ArrayAgg('category__related_groups__group__id'),
        )

    def self_attribute_groups(self, obj):
        group_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=({group_id},)), group_name)
            for group_id, group_name in zip(obj.s_attribute_group_id_list, obj.s_attribute_group_names_list)
        ]
        return mark_safe(', '.join(group_links_list))

    self_attribute_groups.short_description = 'Группы атрибутов категории'


class ProductInCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position_product', 'product', 'list_of_product_categories_names')
    readonly_fields = ('product', 'list_of_product_categories_names')
    model = ProductInCategory
    sortable_field_name = "position_product"
    ordering = ('position_product',)
    extra = 0
    verbose_name_plural = 'Порядок товаров в категории'
    verbose_name = 'Товар'
    can_delete = False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(product_categories_names_list=ArrayAgg('product__related_categories__category__name'))

    def list_of_product_categories_names(self, obj):
        return mark_safe(', '.join(obj.product_categories_names_list))

    list_of_product_categories_names.short_description = "Категории в которые входит товар"


class AttrGroupInCategoryInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = (('position', 'group', 'self_attributes_links',),)
    # fields = (('position', 'group', ),)
    readonly_fields = ('self_attributes_links',)
    model = AttrGroupInCategory
    sortable_field_name = "position"
    autocomplete_fields = ('group',)
    # classes = ['collapse']
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # sq = Attribute.objects.filter('related_groups__group')
        return queryset.annotate(
            s_attributes_names_list=ArrayAgg('group__related_attributes__attribute__name'),
            s_attributes_id_list=ArrayAgg('group__related_attributes__attribute__id')
        )

    def self_attributes_links(self, obj):
        attr_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=(attr_id,)), attr_name)
            for attr_id, attr_name in zip(obj.s_attributes_id_list, obj.s_attributes_names_list)
        ]
        return mark_safe(', '.join(attr_links_list))

    self_attributes_links.short_description = 'Содержит атрибуты'


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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # sq = Attribute.objects.filter('related_groups__group')
        return queryset.annotate(
            s_attributes_names_list=ArrayAgg('group__related_attributes__attribute__name'),
            s_attributes_id_list=ArrayAgg('group__related_attributes__attribute__id')
        )

    def self_attributes_links(self, obj):
        attr_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=(attr_id,)), attr_name)
            for attr_id, attr_name in zip(obj.s_attributes_id_list, obj.s_attributes_names_list)
        ]
        return mark_safe(', '.join(attr_links_list))

    self_attributes_links.short_description = 'Содержит атрибуты'


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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = AttributesInGroup.objects.filter(group__in=request._obj_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PricesOtherShopInline(nested_admin.NestedTabularInline):
    model = PricesOtherShop
    fields = ('created', 'shop', 'price', 'updated', 'url', 'info')
    readonly_fields = ('created', 'updated',)
    extra = 0


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
    list_display = ('tree_actions', 'indented_title', 'self_attribute_groups',)
    model = Category
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('id', 'created', 'updated', 'self_attribute_groups',)
    inlines = (
        ShotParametersOfProductInline, MiniParametersOfProductInline, AttrGroupInCategoryInline,
        ProductInCategoryInLine)

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            request._obj_ = AttrGroupInCategory.objects.filter(category_id=obj.id).values_list('id', flat=True)
        else:
            request._obj_ = []
        return super(CategoryModelAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # sq = AttrGroup.objects.filter(related_categories__category_id=OuterRef('id')).values('id', 'name')
        return queryset.annotate(
            # s_attribute_group_data_list=ArrayAgg(Row),
            s_attribute_group_names_list=ArrayAgg('related_groups__group__name'),
            s_attribute_group_id_list=ArrayAgg('related_groups__group__id'),
        )

    def self_attribute_groups(self, obj):
        # group_links_list = [
        #     "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=({group_id},)), group_name)
        #     for group_id, group_name in zip(obj.s_attribute_group_id_list, obj.s_attribute_group_names_list)
        # ]
        group_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=({group_id},)), group_name)
            for group_id, group_name in zip(obj.s_attribute_group_id_list, obj.s_attribute_group_names_list)
        ]
        return mark_safe(', '.join(group_links_list))

    self_attribute_groups.short_description = "Группыы атрибутов категории--"


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
    list_display = ('art', 'name', 'rating', 'list_of_product_categories_names', 'is_active')
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(product_categories_names_list=ArrayAgg('related_categories__category__name'))

    def list_of_product_categories_names(self, obj):
        return mark_safe(', '.join(obj.product_categories_names_list))

    list_of_product_categories_names.short_description = "Категории в которые входит товар"

    @staticmethod
    def get_addict_attributes_data_value_strings(attrs_data_obj_sorted_list):
        return mark_safe('<br>'.join([
            "%s - %s" % (
                attr_data.name,
                ', '.join(attr_data.value_str) if isinstance(attr_data.value_str, list) else attr_data.value_str)
            for attr_data in attrs_data_obj_sorted_list]))

    def get_shot_parameters_admin_field(self, obj):
        return self.get_addict_attributes_data_value_strings(obj.sorted_shot_attributes)

    get_shot_parameters_admin_field.short_description = "Краткие характеристики товара"

    def get_mini_parameters_admin_field(self, obj):
        return self.get_addict_attributes_data_value_strings(obj.sorted_mini_attributes)

    get_mini_parameters_admin_field.short_description = "Характеристики на выдаче категории"


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
            if obj.related_attributes.exists():
                attr_in_group_copy_list = []
                for attr_in_group_item in obj.related_attributes.all():
                    copy_attr_in_group_item = copy.copy(attr_in_group_item)
                    copy_attr_in_group_item.id = None
                    copy_attr_in_group_item.group = group_copy
                    attr_in_group_copy_list.append(copy_attr_in_group_item)
                AttributesInGroup.objects.bulk_create(attr_in_group_copy_list)
            return HttpResponseRedirect(reverse('admin:products_attrgroup_change', args=(group_copy.id,)))
        return super().response_change(request, obj)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            s_attributes_names_list=ArrayAgg('related_attributes__attribute__name'),
            s_attributes_id_list=ArrayAgg('related_attributes__attribute__id'),
        )

    def self_attributes_links(self, obj):
        attr_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attribute_change', args=(attr_id,)), attr_name)
            for attr_id, attr_name in zip(obj.s_attributes_id_list, obj.s_attributes_names_list)
        ]
        return mark_safe(', '.join(attr_links_list))

    self_attributes_links.short_description = 'Содержит атрибуты'


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
