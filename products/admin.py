from django.contrib.postgres import fields
from django_json_widget.widgets import JSONEditorWidget
from mptt.admin import TreeRelatedFieldListFilter, DraggableMPTTAdmin
import copy
from django.contrib import admin
from django.http import HttpResponseRedirect
from django_summernote.admin import SummernoteModelAdmin
from grappelli.forms import GrappelliSortableHiddenMixin
from .admin_form import *


class ProductImageInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    fields = ['position', ('image_image', 'image', 'name', 'is_main_1', 'is_main_2', 'is_active')]
    readonly_fields = ["image_image"]
    model = ProductImage
    sortable_field_name = "position"
    extra = 0

    def image_image(self, obj):
        return mark_safe('<img src="{url}" width=95 height=95/>'.format(url=obj.image.url))


class BrandInLine(admin.TabularInline):
    model = Brand
    extra = 0


class CategoryForProductInLine(GrappelliSortableHiddenMixin, admin.TabularInline):
    formset = CategoryForProductInLineFormSet
    fields = ('position_category', 'category', 'self_attribute_group')
    readonly_fields = ('self_attribute_group',)
    model = ProductInCategory
    sortable_field_name = "position_category"
    # classes = ['collapse']
    extra = 0


class ProductInCategoryInLine(admin.StackedInline):
    # class ProductInCategoryInLine(GrappelliSortableHiddenMixin, admin.StackedInline):
    fields = ('position_product', 'product',)
    readonly_fields = ('product',)
    model = ProductInCategory
    sortable_field_name = "position_product"
    # classes = ['collapse']
    extra = 0


class AttrGroupInCategoryInline(admin.TabularInline):
    # class AttrGroupInCategoryInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    fields = (('position', 'group', 'self_attributes_links',),)
    readonly_fields = ('self_attributes_links',)
    model = AttrGroupInCategory
    sortable_field_name = "position"
    autocomplete_fields = ('group',)
    # classes = ['collapse']
    extra = 0


class CategoriesInGroupInline(admin.TabularInline):
    fields = ('position', 'category',)
    model = AttrGroupInCategory
    formset = CategoriesInGroupInlineFormSet
    ordering = ('category',)
    extra = 0
    verbose_name = "Категория товаров содержащая текущую группу атрибутов"
    verbose_name_plural = "Категории товаров содержащие текущую группу атрибутов"


class AttributesInGroupInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    fields = ('position', 'attribute', 'type_of_value', 'self_value_variants')
    readonly_fields = ('type_of_value', 'self_value_variants',)
    model = AttributesInGroup
    sortable_field_name = "position"
    extra = 0
    autocomplete_fields = ('attribute',)
    form = AttributeForm


class ItemOfCustomOrderGroupInline(admin.TabularInline):
    fields = ('position', 'category', 'group', 'getlink_group', 'self_attributes_links',)
    readonly_fields = ('self_attributes_links', 'getlink_group',)
    model = ItemOfCustomOrderGroup
    formset = ItemOfCustomOrderGroupInLineFormSet
    sortable_field_name = "position"
    extra = 0
    ordering = ("position",)
    can_delete = False


class ShotParametersOfProductInline(GrappelliSortableHiddenMixin, admin.StackedInline):
    fields = ('position', 'attribute', 'name', 'is_active')
    extra = 0
    model = ShotParametersOfProduct
    ordering = ("position",)

    # classes = ['collapse']
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = AttributesInGroup.objects.filter(group__in=request._obj_).order_by('group')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MiniParametersOfProductInline(GrappelliSortableHiddenMixin, admin.StackedInline):
    fields = ('position', 'attribute', 'name', 'is_active')
    extra = 0
    model = MiniParametersOfProduct
    ordering = ("position",)

    # classes = ['collapse']
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = AttributesInGroup.objects.filter(group__in=request._obj_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryModelAdmin(SummernoteModelAdmin, DraggableMPTTAdmin, ):
    fields = (
        ('name', 'parent'), ('slug', 'id', 'is_active'), ('image', 'image_view',), ('sign', 'sign_view'), 'description',
        ('created', 'updated'))
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

    def image_view(self, obj):
        return mark_safe('<img src="{url}" width=95 height=95/>'.format(url=obj.image.url))

    def sign_view(self, obj):
        return mark_safe('<img src="{url}" width=40 height=40/>'.format(url=obj.sign.url))


@admin.register(Product)
class ProductModelAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }
    form = ProductForm
    list_display = ('art', 'name', 'rating', 'get_product_category_link', 'is_active')
    list_display_links = ('name',)
    list_editable = ('rating', 'is_active',)
    model = Product
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('created', 'updated', 'category_collection', 'get_category_collection_link',)
    list_filter = (('admin_category', TreeRelatedFieldListFilter),)
    inlines = (ProductImageInline, CategoryForProductInLine)
    change_form_template = "products/product_changeform.html"
    fieldsets = (
        (None, {
            'fields': (
                'category_collection', 'get_category_collection_link', ('name', 'art',), ('slug', 'admin_category'),
                ('brand', 'is_active',),
                ('created', 'updated',), 'is_active_custom_order_group')
        }),
        ("Характеристики", {
            # 'classes': ('collapse',),
            'fields': ('parameters', 'parameters_structure'),
        }),
        ("Габбариты", {'fields': (('lenght', 'width', 'height',), ('lenght_box', 'width_box', 'height_box'))}),
        ("Разное", {
            'fields': (('weight', 'warranty',),),
            # 'classes': ('wide,')
        }),
        (None, {
            'fields': ('description',)
        })
    )

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            obj.save()
            product_copy = copy.copy(obj)
            product_copy.id = None
            product_copy.slug = None
            product_copy.art = None

            copies = [0]
            for prod in Product.objects.filter(name__startswith=obj.name + ' (@копия #'):
                left_part_name = prod.name[(prod.name.find(' (@копия #') + 10):]
                number_of_copy = int(left_part_name[:left_part_name.find(')')])
                copies.append(number_of_copy)
            product_copy.name = obj.name + ' (@копия #%s)' % (max(copies) + 1)
            product_copy.save()
            for cat in Category.objects.filter(related_products__product_id=obj.id):
                ProductInCategory.objects.create(product=product_copy, category=cat)
            for ph in obj.productimage_set.all():
                ProductImage.objects.create(product=product_copy, image=ph.image)
            return HttpResponseRedirect(reverse('admin:products_product_change', args=(product_copy.id,)))
        return super().response_change(request, obj)

    def image_view(self, obj):
        return mark_safe('<img src="{url}" width=95 height=95/>'.format(url=obj.image.url))


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    fields = ('name', 'slug', 'is_active')
    inlines = (BrandInLine,)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AttrGroup)
class AttrGroupAdmin(admin.ModelAdmin):
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
            obj.save()
            group_copy = copy.copy(obj)
            group_copy.id = None
            group_copy.slug = None
            copies = [0]
            for group in AttrGroup.objects.filter(name__startswith=obj.name + ' (@копия #'):
                left_part_name = group.name[(group.name.find(' (@копия #') + 10):]
                number_of_copy = int(left_part_name[:left_part_name.find(')')])
                copies.append(number_of_copy)
            group_copy.name = obj.name + ' (@копия #%s)' % (max(copies) + 1)
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
            obj.save()
            attribute_copy = copy.copy(obj)
            attribute_copy.id = None
            attribute_copy.slug = None
            attribute_copy.name = obj.name + ' (@копия #%s)' % (obj.get_other_copy + 1)
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
class CategoryCollectionAdmin(admin.ModelAdmin):
    fields = ('id', 'category_list', ('is_active_custom_order_group', 'is_active_custom_order_shot_parameters',
                                      'is_active_custom_order_mini_parameters',),)
    readonly_fields = ('id',)
    model = CategoryCollection
    form = CategoryCollectionForm
    inlines = (ItemOfCustomOrderGroupInline,)


admin.site.register(ProductImage)
admin.site.register(Brand)
