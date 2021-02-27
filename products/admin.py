import nested_admin
# from django.db.models import Subquery, OuterRef, JSONField
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.http import HttpResponseRedirect

from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter

from .admin_form import AttrGroupForm, AttributeForm, CategoriesInGroupInlineFormSet, CategoryCollectionForm, \
    CategoryForProductInLineFormSet, ItemOfCustomOrderGroupInLineFormSet, ProductForm

from .models import *
from django.contrib.postgres.aggregates import ArrayAgg

from .services import get_related_objects_list_copies, save_and_make_copy, remove_attr_data_from_products
from django.utils.encoding import force_str


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
        return "нет групп атрибутов" if obj.s_attribute_group_id_list == [None] else mark_safe(
            ', '.join(group_links_list))

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
        return "нет атрибутов" if obj.s_attributes_id_list == [None] else mark_safe(', '.join(attr_links_list))

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            s_value_variants_names_list=ArrayAgg('attribute__value_list__name'),
            s_value_variants_id_list=ArrayAgg('attribute__value_list__id'),)

    def self_value_variants(self, obj):
        value_variants_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attributevalue_change', args=(variant_id,)), variant_name)
            for variant_id, variant_name in zip(obj.s_value_variants_id_list, obj.s_value_variants_names_list)]
        return "" if obj.s_value_variants_id_list == [None] else mark_safe(
            ', '.join(value_variants_links_list))

    self_value_variants.short_description = "Варианты значений"


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


class ItemOfCustomOrderShotParametersInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'category', 'attribute', )
    readonly_fields = ('category', 'attribute',)
    model = ItemOfCustomOrderShotParameters
    formset = ItemOfCustomOrderGroupInLineFormSet
    sortable_field_name = "position"
    ordering = ('position',)
    extra = 0

class ItemOfCustomOrderMiniParametersInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ('position', 'category', 'attribute', )
    readonly_fields = ('category', 'attribute',)
    model = ItemOfCustomOrderMiniParameters
    formset = ItemOfCustomOrderGroupInLineFormSet
    sortable_field_name = "position"
    ordering = ('position',)
    extra = 0


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
        return queryset.annotate(
            s_attribute_group_names_list=ArrayAgg('related_groups__group__name'),
            s_attribute_group_id_list=ArrayAgg('related_groups__group__id'),)

    def self_attribute_groups(self, obj):
        group_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attrgroup_change', args=(group_id,)), group_name)
            for group_id, group_name in zip(obj.s_attribute_group_id_list, obj.s_attribute_group_names_list)]
        return "Нет групп атрибутов" if obj.s_attribute_group_id_list == [None] else mark_safe(
            ', '.join(group_links_list))

    self_attribute_groups.short_description = "Группыы атрибутов категории--"

    def delete_selected_tree(self, modeladmin, request, queryset):
        """
        Deletes multiple instances and makes sure the MPTT fields get
        recalculated properly. (Because merely doing a bulk delete doesn't
        trigger the post_delete hooks.)
        """
        # If this is True, the confirmation page has been displayed
        if request.POST.get("post"):
            print(f'delete_selected queryset - {queryset}')
            n = 0
            with queryset.model._tree_manager.delay_mptt_updates():
                for obj in queryset:
                    if self.has_delete_permission(request, obj):
                        obj_display = force_str(obj)
                        self.log_deletion(request, obj, obj_display)
                        self.delete_model(request, obj)
                        n += 1
            self.message_user(
                request, "Успешно удалено %(count)d узлов." % {"count": n}
            )
            # Return None to display the change list page again
            return None
        else:
            # (ab)using the built-in action to display the confirmation page
            return delete_selected(self, request, queryset)

    def delete_model(self, request, obj):
        print(f'DELETE CAT - {obj}')
        # Перебрать коллекции категорий. Если при отвязке категории коллекция с остается с менее чем двумя категориями
        # или коллекция с уменьшенным набором уже существует то коллекцию удалить. Иначе у коллекции удалить айтемы
        # групп атрибутов связанные с удаленной категорией. В функцию remove_attr_data_from_products передать список
        # из двух элементов: список удаленных коллекций и список модифицированных коллекций.

        all_data_to_update = remove_attr_data_from_products(category=obj)
        if all_data_to_update.products_list != [] and all_data_to_update.fields_names_list != []:
            Product.objects.bulk_update(all_data_to_update.products_list, list(
                set(all_data_to_update.fields_names_list)))
        obj.delete()


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
                'order-0', 'baton-tabs-init', 'baton-tab-inline-related_categories', 'baton-tab-inline-related_image',
                'baton-tab-inline-pricesothershop',),
        }),

    )

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            product_copy = save_and_make_copy(obj, Product)
            product_copy.art = None
            product_copy.url = None
            product_copy.save()
            if obj.related_categories.exists():
                ProductInCategory.objects.bulk_create(
                    get_related_objects_list_copies(obj.related_categories.all(), 'product_id', product_copy.id)
                )
            if obj.related_image.exists():
                ProductImage.objects.bulk_create(
                    get_related_objects_list_copies(obj.related_image.all(), 'product_id', product_copy.id))
            return HttpResponseRedirect(reverse('admin:products_product_change', args=(product_copy.id,)))
        return super().response_change(request, obj)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(product_categories_names_list=ArrayAgg('related_categories__category__name'))

    def list_of_product_categories_names(self, obj):
        return "нет категорий" if obj.product_categories_names_list == [None] else mark_safe(
            ', '.join(obj.product_categories_names_list))

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
                AttributesInGroup.objects.bulk_create(
                    get_related_objects_list_copies(obj.related_attributes.all(), 'group_id', group_copy.id)
                )
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
        return "Нет атрибутов" if obj.s_attributes_id_list == [None] else mark_safe(', '.join(attr_links_list))

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            s_value_variants_names_list=ArrayAgg('value_list__name'),
            s_value_variants_id_list=ArrayAgg('value_list__id'),)

    def self_value_variants(self, obj):
        value_variants_links_list = [
            "<a href=%s>%s</a>" % (reverse('admin:products_attributevalue_change', args=(variant_id,)), variant_name)
            for variant_id, variant_name in zip(obj.s_value_variants_id_list, obj.s_value_variants_names_list)]
        return "" if obj.s_value_variants_id_list == [None] else mark_safe(
            ', '.join(value_variants_links_list))

    self_value_variants.short_description = "Варианты значений"


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
    inlines = (ItemOfCustomOrderGroupInline, ItemOfCustomOrderShotParametersInline,
               ItemOfCustomOrderMiniParametersInline)


@admin.register(SomeSites)
class SomeSitesAdmin(nested_admin.NestedModelAdmin):
    model = SomeSites


admin.site.register(ProductImage)
admin.site.register(Brand)
