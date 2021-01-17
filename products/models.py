from collections import namedtuple
from operator import attrgetter

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils.safestring import mark_safe
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from .utils import get_unique_slug


class Category(MPTTModel):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    parent = TreeForeignKey('self', blank=True, null=True, default=None, on_delete=models.CASCADE,
                            related_name='children', db_index=True, verbose_name='Родительская категория')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Описание категории')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name='Фото категории')
    sign = models.ImageField(upload_to='category_sign/', blank=True, null=True, verbose_name='Значек категории')

    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        for prod in self.related_products.all():
            prod.delete_attributes()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = get_unique_slug(self, 'name', 'slug')
        super().save(*args, **kwargs)

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['name']

    def self_attribute_group(self):
        group_links = [
            "<a href={}>{}</a>".format(reverse('admin:products_attrgroup_change', args=(i.group_id,)), i.group)
            for i in self.related_groups.all()
        ]
        return mark_safe(', '.join(group_links))
    self_attribute_group.short_description = 'Группы атрибутов'
    self_attribute_group = property(self_attribute_group)

    @property
    def getlink(self):
        link = "<a href={}>{}</a>".format(reverse('admin:products_category_change', args=(self.id,)), self.name)
        return mark_safe(link)

    def have_children(self):
        return self.children.filter(is_active=True).exists()

    def children_category(self):
        return self.children.filter(is_active=True)

    children_category = property(children_category)


class Product(models.Model):
    RATING = (
        (1, " * "),
        (2, " * * "),
        (3, " * * * "),
        (4, " * * * * "),
        (5, " * * * * * ")
    )
    WARRANTY = (
        (1, "12 мес."),
        (2, "6 мес."),
        (3, "3 мес."),
        (4, "14 дней"),
    )
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    art = models.CharField(max_length=10, blank=True, null=True, default=None, unique=True,
                           verbose_name='Артикул товара')
    made_in = models.ForeignKey('Country', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                verbose_name='Страна производства')
    brand = models.ForeignKey('Brand', blank=True, null=True, default=None, on_delete=models.CASCADE,
                              verbose_name='Торговая марка')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Описание товара')
    rating = models.SmallIntegerField(choices=RATING, default=1, db_index=True)
    admin_category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                    verbose_name='Категория товаров админ-панели')
    category_collection = models.ForeignKey('CategoryCollection', blank=True, null=True, default=None,
                                            on_delete=models.SET_NULL, verbose_name='Коллекция категорий')

    parameters = models.JSONField(default=dict, blank=True, verbose_name='Характеристики товара')
    parameters_structure = models.JSONField(default=dict, blank=True, verbose_name='')
    sorted_parameters_structure = models.JSONField(default=list, blank=True,
                                                   verbose_name='Сортированная структура характеристик')

    custom_order_group = models.JSONField(default=list, blank=True,
                                          verbose_name='Индивидуальный порядок групп атрибутов для сочетания категорий')
    is_active_custom_order_group = models.BooleanField(default=True,
                                                       verbose_name='Использоватть порядок групп атрибутов '
                                                                    'определенный в коллекции категорий')

    shot_parameters_structure = models.JSONField(default=dict, blank=True,
                                                 verbose_name='Структура кратких характеристик товара')
    mini_parameters_structure = models.JSONField(default=dict, blank=True,
                                                 verbose_name='Структура мини характеристик товара')
    shot_parameters_custom_structure = models.JSONField(default=dict, blank=True,
                                                        verbose_name='Структура кратких характеристик товара для '
                                                                     'сочетания категорий')
    mini_parameters_custom_structure = models.JSONField(default=dict, blank=True,
                                                        verbose_name='Структура мини характеристик товара для '
                                                                     'сочетания категорий')

    lenght = models.FloatField(blank=True, null=True, verbose_name='Длина, см')
    width = models.FloatField(blank=True, null=True, verbose_name='Ширина, см')
    height = models.FloatField(blank=True, null=True, verbose_name='Высота, см')
    lenght_box = models.FloatField(blank=True, null=True, verbose_name='Длина упаковки, см')
    width_box = models.FloatField(blank=True, null=True, verbose_name='Ширина упаковки, см')
    height_box = models.FloatField(blank=True, null=True, verbose_name='Высота упаковки, см')
    weight = models.FloatField(blank=True, null=True, verbose_name='Вес, кг')
    warranty = models.SmallIntegerField(choices=WARRANTY, default=1, verbose_name='Срок гарантии')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на товар на сайте производителя)')

    class Meta:
        ordering = ['name']
        verbose_name = "Товар"
        verbose_name_plural = "Список товаров"

    def __str__(self):
        return self.name

    def get_category_collection_link(self):
        # if self.category_collection_id is not None:
        if self.category_collection_id:
            return mark_safe("<a href={}>{}</a>".format(
                reverse('admin:products_categorycollection_change', args=(self.category_collection_id,)),
                self.category_collection))
        else:
            return "Не назначена"

    get_category_collection_link.short_description = 'Коллекия категорий'
    get_category_collection_link = property(get_category_collection_link)

    def get_product_category_link(self):
        categories_link_list = []
        for cat in Category.objects.filter(related_products__product=self):
            category_link = "<a href={}>{}</a>".format(reverse('admin:products_category_change', args=(cat.id,)),
                                                       cat.name)
            categories_link_list.append(category_link)
        return mark_safe(', '.join(categories_link_list))

    get_product_category_link.short_description = 'Дополнительные категории'
    get_product_category_link = property(get_product_category_link)

    @property
    def get_link_refresh(self):
        return "<a href={}>{}</a>".format(reverse('admin:products_product_change', args=(self.id,)), 'Обновить')

    @staticmethod
    def get_sorted_addict_attr(attr_field):
        attribute_data = namedtuple('attribute_data', 'pos name full_id id value_str value')
        parameters_srt = sorted([
            [  # одна из категорий [id: {'cat_position': pos, "shot_attributes": {}]
                cat['cat_position'],
                sorted([
                    attribute_data(
                        attr[1]['pos_atr'],
                        Attribute.objects.get(pk=attr[1]['id']).name if (attr[1]['name'] is None) else attr[1]['name'],
                        attr[0],  # full_id для получения значения атрибута
                        attr[1]['id'],
                        attr[1]['value_str'],
                        attr[1]['value']
                    )
                    for attr in cat['attributes'].items()],  # список  атрибутов в категории attr
                    key=attrgetter('pos'))  # сортировать по ключу 'pos'
            ]
            for cat in attr_field.values()])
        return parameters_srt

    @property
    def sorted_shot_attributes(self):
        return self.get_sorted_addict_attr(self.shot_parameters_structure)

    @property
    def sorted_mini_attributes(self):
        return self.get_sorted_addict_attr(self.mini_parameters_structure)

    @staticmethod
    def reformat_addict_attr_for_admin(attrs_sorted):
        parameters_display = map(
            lambda cat: '<br>'.join(list(map(
                lambda attr_data: '%s - %s' % (
                    attr_data.name,
                    ', '.join(attr_data.value_str) if isinstance(attr_data.value_str, list)
                    else attr_data.value_str
                ),
                cat[1]))),  # категория без порядкового номера
            attrs_sorted)  # отсортированый перечень категорий
        return mark_safe('<br>'.join(list(parameters_display)))

    def get_shot_parameters_admin_field(self):
        return self.reformat_addict_attr_for_admin(self.sorted_shot_attributes)

    get_shot_parameters_admin_field.short_description = "Краткие характеристики товара"
    get_shot_parameters_admin_field = property(get_shot_parameters_admin_field)

    def get_mini_parameters_admin_field(self):
        return self.reformat_addict_attr_for_admin(self.sorted_mini_attributes)

    get_mini_parameters_admin_field.short_description = "Характеристики на выдаче категории"
    get_mini_parameters_admin_field = property(get_mini_parameters_admin_field)


class ProductImage(models.Model):
    name = models.CharField(max_length=128, blank=True, default='', db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Фото товара')
    is_main_1 = models.BooleanField(default=True, verbose_name='Главное фото')
    is_main_2 = models.BooleanField(default=True, verbose_name='Главное фото при наведении')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товаров"

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    slug = models.SlugField(max_length=64, blank=True, null=True, default=None, unique=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    country = models.ForeignKey(Country, blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Страна брэнда')

    class Meta:
        verbose_name = "Торговая марка"
        verbose_name_plural = "Торговые марки"

    def __str__(self):
        return f'{self.name} ({self.country})'


class ProductInCategory(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Товар',
                                related_name='related_categories')
    category = TreeForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория',
                              related_name='related_products')
    position_category = models.PositiveIntegerField("PositionCategory", default=0)
    position_product = models.PositiveIntegerField("PositionProduct", default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_category = self.category_id

    class Meta:
        verbose_name = "Размещение товара в категории "
        verbose_name_plural = "Размещения товара в категории"
        unique_together = ('product', 'category')

    def __str__(self):
        name = Product.objects.filter(id=self.product_id).values_list('name', flat=True)[0]
        category = Category.objects.filter(id=self.category_id).values_list('name', flat=True)[0]
        return f'"{category}" - {name}'

    def get_product_category_link(self):
        return self.product.get_product_category_link

    get_product_category_link.short_description = 'Дополнительные категории'
    get_product_category_link = property(get_product_category_link)

    def self_attribute_group(self):
        return self.category.self_attribute_group

    self_attribute_group.short_description = 'Группы атрибутов'
    self_attribute_group = property(self_attribute_group)

    # def clean(self):
    #     # optimized version
    #     groups_in_this_category = AttrGroup.objects.filter(related_categories__category=self.category_id)
    #     categories_this_product = self.product.related_categories.exclude(id=self.id).values_list('category', flat=True)
    #     other_groups_allredy_in_product = AttrGroup.objects.filter(
    #         related_categories__category__id__in=categories_this_product)
    #     common_groups = groups_in_this_category.intersection(other_groups_allredy_in_product)
    #     if common_groups.exists():
    #         common_groups_names = common_groups.values_list('name', flat=True)
    #         raise ValidationError(
    #             'Новое значение содержит категорию или товар с дублирующейся группой атрибутов: "%s"' % ', '.join(
    #                 common_groups_names)
    #         )

    def create_attributes(self):
        if self.category.related_groups.filter(group__related_attributes__isnull=False):
            category_id = str(self.category_id)
            self.product.parameters_structure[category_id] = {'cat_position': self.position_category,
                                                              'groups_attributes': {}}
            for group_in_cat in self.category.related_groups.filter(
                    group__related_attributes__isnull=False).select_related('group'):
                group_id = str(group_in_cat.group_id)
                self.product.parameters_structure[category_id]['groups_attributes'][group_id] = {
                    'group_position': group_in_cat.position, 'attributes': {}}
                for atr_group in group_in_cat.group.related_attributes.select_related('attribute').all():
                    atr_id = str(atr_group.attribute_id)
                    if not '%s-%s' % (group_id, atr_id) in self.product.parameters.keys():
                        self.product.parameters['%s-%s' % (group_id, atr_id)] = None
                    self.product.parameters_structure[category_id]['groups_attributes'][group_id]['attributes'][
                        atr_id] = {'atr_position': atr_group.position}
        self.product.save()
        # добавить соответствующую коллекцию категорий - сделано в BaseInlineFormSet

    def delete_attributes(self):
        category_id = str(self.category_id)
        if category_id in self.product.parameters_structure.keys():
            self.product.parameters_structure.pop(category_id)
        for group in AttrGroup.objects.filter(related_categories__category=self.category_id).only('id'):
            group_id = str(group.id)
            for atr in Attribute.objects.filter(related_groups__group=group_id).only('id'):
                atr_id = str(atr.id)
                if (full_id := f'{group_id}-{atr_id}') in self.product.parameters:
                    self.product.parameters.pop(full_id)
        self.product.save()
        # сделать удаление коллекции категорий из товара - сделано в BaseInlineFormSet

    def save(self, *args, **kwargs):
        self.product.refresh_from_db()
        max_product_position = ProductInCategory.objects.filter(category_id=self.category_id).aggregate(
            Max('position_product'))
        if not self.id or self.category_id != self.old_category:
            # if 0:
            if max_product_position['position_product__max'] is not None:
                self.position_product = max_product_position['position_product__max'] + 1
            else:
                self.position_product = 0
        if self.old_category is not None and self.old_category != self.category_id:
            old_category_id = str(self.old_category)
            if old_category_id in self.product.parameters_structure.keys():
                self.product.parameters_structure.pop(old_category_id)
            for group in AttrGroup.objects.filter(related_categories__category=self.old_category).values('id'):
                for atr in Attribute.objects.filter(related_groups__group=group['id']).values('id'):
                    self.product.parameters.pop(f"{group['id']}-{atr['id']}")
        super().save(*args, **kwargs)
        self.create_attributes()
        # сделать удаление коллекции категорий и добавление новой - сделано в BaseInlineFormSet

    def delete(self, *args, **kwargs):
        self.delete_attributes()
        super().delete(*args, **kwargs)


class AttrGroup(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)

    class Meta:
        verbose_name = "Группа атрибутов"
        verbose_name_plural = "Группы атрибутов"

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        for group_cat in self.related_categories.all():
            group_cat.delete_attributes()
        super().delete(*args, **kwargs)

    @property
    def getlink(self):
        link = "<a href={}>{}</a>".format(reverse('admin:products_attrgroup_change', args=(self.id,)), self.name)
        return mark_safe(link)

    def self_attributes_links(self):
        ls = []
        for i in self.related_attributes.all().order_by('position'):
            link_atr = "<a href={}>{}</a>".format(reverse('admin:products_attribute_change', args=(i.attribute.id,)),
                                                  i.attribute.name)
            ls.append(link_atr)
        return mark_safe(', '.join(ls))

    self_attributes_links.short_description = 'Содержит атрибуты'
    self_attributes_links = property(self_attributes_links)


TYPE_OF_VALUE = (
    (1, "Текст"),
    (2, "Целое положит. число"),
    (3, "Число"),
    (4, "Логический тип"),
    (5, "Вариант из фикс. значений"),
    (6, "Набор фикс. значений")
)


class Attribute(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    position = models.PositiveIntegerField("Position", blank=True, null=True)
    type_of_value = models.SmallIntegerField(choices=TYPE_OF_VALUE, default=1, verbose_name='Тип данных')
    value_list = models.ManyToManyField('AttributeValue', blank=True, default=None, verbose_name='Список значений')

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"
        ordering = ['position']

    def __str__(self):
        return self.name

    def delete_attributes(self):
        for atr in self.related_groups.all():
            atr.delete_attributes()

    def delete(self, *args, **kwargs):
        self.delete_attributes()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = get_unique_slug(self, 'name', 'slug')
        super().save(*args, **kwargs)

    @property
    def getlink(self):
        link = "<a href={}>{}</a>".format(reverse('admin:products_attribute_change', args=(self.id,)), self.name)
        return mark_safe(link)

    def self_value_variants(self):
        values = self.value_list.all()
        ls = []
        for i in values:
            link_val = "<a href={}>{}</a>".format(reverse('admin:products_attributevalue_change', args=(i.id,)), i)
            ls.append(link_val)
        return mark_safe(', '.join(ls))

    self_value_variants.short_description = 'Список значений '
    self_value_variants = property(self_value_variants)


class AttributeValue(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)

    class Meta:
        verbose_name = "Значение атрибутов"
        verbose_name_plural = "Значения атрибутов"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = get_unique_slug(self, 'name', 'slug')
        super().save(*args, **kwargs)


class AttrGroupInCategory(models.Model):
    category = TreeForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE,
                              verbose_name='Категория товаров', related_name='related_groups')
    group = models.ForeignKey(AttrGroup, blank=True, null=True, on_delete=models.CASCADE,
                              verbose_name='Группа атрибутов', related_name='related_categories')
    position = models.PositiveIntegerField("Position", blank=True, null=True, default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_category = self.category_id
        self.old_group = self.group_id

    class Meta:
        verbose_name = "Группа атрибутов категории"
        verbose_name_plural = "Группы атрибутов категории"
        ordering = ['position']
        unique_together = ('category', 'group')

    def __str__(self):
        return self.group.name

    def clean(self):
        # ищем товары для которых в их других категриях уже есть эта группа атрибутов
        products_this_category = Product.objects.filter(related_categories__category__id=self.category_id)
        other_category_related_products = Category.objects.filter(
            related_products__product__in=products_this_category).exclude(id=self.category_id)
        if self.old_category:
            other_category_related_products = other_category_related_products.exclude(id=self.old_category)
        other_group_related_products = AttrGroup.objects.filter(
            related_categories__category__in=other_category_related_products)
        if self.group in other_group_related_products:
            raise ValidationError(
                f"Невозможно добавить группу атрибутов {self.group} к категории {self.category} так как она будет "
                f"дублироваться для некоторых товаров:"
            )

    def get_self_atr_structure_list(self):
        attributes_list_structure = {}
        for atr_in_gr in AttributesInGroup.objects.filter(group=self.group_id).values_list('attribute_id', 'position'):
            attributes_list_structure[str(atr_in_gr[0])] = atr_in_gr[1]
        return attributes_list_structure

    # bulk edition
    def create_attributes(self):
        group_id = str(self.group_id)
        products_for_update = []
        for prod in self.category.related_products.only('product').select_related('product').all():
            product = prod.product
            category_id = str(self.category_id)
            category_position = prod.position_category
            if category_id not in product.parameters_structure.keys():
                product.parameters_structure[category_id] = {'cat_position': category_position, 'groups_attributes': {}}
            if self.group.related_attributes.exists():
                product.parameters_structure[category_id]['groups_attributes'][group_id] = {
                    'group_position': self.position, 'attributes': {}}
            for atr_id, position in self.get_self_atr_structure_list().items():
                product.parameters_structure[category_id]['groups_attributes'][group_id]['attributes'][atr_id] = {
                    'atr_position': position}
                if not (full_id := f'{group_id}-{atr_id}') in product.parameters.keys():
                    product.parameters[full_id] = None
            products_for_update.append(product)
        Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])
        # добавить в группу в коллекции категорий

    # bulk edition
    def delete_attributes(self):
        category_id = str(self.category_id)
        group_id = str(self.group_id)
        products_for_update = []
        for product in Product.objects.filter(related_categories__category=self.category).only('parameters_structure',
                                                                                               'parameters'):
            if category_id in product.parameters_structure and group_id in product.parameters_structure[category_id][
                'groups_attributes']:
                product.parameters_structure[category_id]['groups_attributes'].pop(group_id)
            if not product.parameters_structure[category_id]['groups_attributes']:
                product.parameters_structure.pop(category_id)
            for atr_id in self.get_self_atr_structure_list().keys():
                product.parameters.pop('%s-%s' % (group_id, atr_id))
            products_for_update.append(product)
        Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])

    # bulk edition
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        category_id = str(self.category_id)
        if self.old_group is not None and self.old_group != self.group_id:
            old_group_id = str(self.old_group)
            attributes_id = []
            products_for_update = []
            for attribute in Attribute.objects.filter(related_groups__group=self.old_group).only('id'):
                attributes_id.append(str(attribute.id))
            for product in Product.objects.filter(related_categories__category=self.category).only(
                    'parameters_structure', 'parameters'):
                product.parameters_structure[category_id]['groups_attributes'].pop(old_group_id)
                if not product.parameters_structure[category_id]['groups_attributes']:
                    product.parameters_structure.pop(category_id)
                for atr_id in attributes_id:
                    product.parameters.pop(f'{old_group_id}-{atr_id}')
                products_for_update.append(product)
            Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])

        if self.old_category is not None and self.old_category != self.category_id:
            old_category_id = str(self.old_category)
            group_attribute_id = str(self.group_id)
            products_for_update = []
            for product in Product.objects.filter(related_categories__category=self.old_category).only(
                    'parameters_structure', 'parameters'):
                product.parameters_structure[old_category_id]['groups_attributes'].pop(group_attribute_id)
                if not product.parameters_structure[old_category_id]['groups_attributes']:
                    product.parameters_structure.pop(old_category_id)
                if not product.related_categories.filter(category=category_id).exists():
                    for atr_id in self.get_self_atr_structure_list().keys():
                        product.parameters.pop(f'{group_attribute_id}-{atr_id}')
                products_for_update.append(product)
            Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])

            for cc in CategoryCollection.objects.filter(category_list=self.old_category):
                cc.update_group_in_product()

        self.create_attributes()
        for cc in CategoryCollection.objects.filter(category_list=self.category):
            max_position = ItemOfCustomOrderGroup.objects.filter(category_collection_id=cc.id).aggregate(
                Max('position'))
            if max_position['position__max'] is None:
                position = 0
            else:
                position = max_position['position__max'] + 1
            ItemOfCustomOrderGroup.objects.create(category_collection_id=cc.id, category=self.category,
                                                  group=self.group, position=position)
            cc.update_group_in_product()

    def delete(self, *args, **kwargs):
        self.delete_attributes()
        super().delete(*args, **kwargs)
        for cc in CategoryCollection.objects.filter(category_list=self.category):
            cc.update_group_in_product()
        ShotParametersOfProduct.objects.filter(attribute__in=self.group.related_attributes.all(),
                                               category=self.category_id).delete()
        MiniParametersOfProduct.objects.filter(attribute__in=self.group.related_attributes.all(),
                                               category=self.category_id).delete()

    def self_attributes_links(self):
        return self.group.self_attributes_links

    self_attributes_links.short_description = ' Содержит атрибуты'
    self_attributes_links = property(self_attributes_links)


class AttributesInGroup(models.Model):
    attribute = models.ForeignKey(Attribute, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Атрибут',
                                  related_name='related_groups')
    group = models.ForeignKey(AttrGroup, blank=True, null=True, on_delete=models.CASCADE,
                              verbose_name='Группа атрибутов', related_name='related_attributes')
    position = models.PositiveIntegerField("Position", null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_attribute = self.attribute_id

    class Meta:
        verbose_name = "Атрибут группы"
        verbose_name_plural = "Атрибуты группы"
        ordering = ['position']
        unique_together = ('attribute', 'group')

    def __str__(self):
        return f"{self.group.name} / {self.attribute.name}"

    def self_value_variants(self):
        return self.attribute.self_value_variants

    self_value_variants.short_description = 'Список значений'
    self_value_variants = property(self_value_variants)

    def type_of_value(self):
        return self.attribute.get_type_of_value_display()

    type_of_value.short_description = 'Тип данных'
    type_of_value = property(type_of_value)

    def create_attributes(self):
        for cat in self.group.related_categories.select_related('category').all():
            category = cat.category
            category_id = str(category.id)
            group_id = str(self.group_id)
            atr_id = str(self.attribute_id)
            products_for_update = []
            for product in Product.objects.filter(related_categories__category=category).only('parameters_structure',
                                                                                              'parameters'):
                if category_id not in product.parameters_structure.keys():
                    product.parameters_structure[category_id] = {'groups_attributes': {}, 'cat_position': cat.position}
                if group_id not in product.parameters_structure[category_id]['groups_attributes'].keys():
                    product.parameters_structure[category_id]['groups_attributes'][group_id] = {'attributes': {},
                                                                                                'group_position':
                                                                                                    cat.position}
                product.parameters_structure[category_id]['groups_attributes'][group_id]['attributes'][atr_id] = {
                    'atr_position': self.position}
                if not (full_id := f'{group_id}-{atr_id}') in product.parameters.keys():
                    product.parameters[full_id] = None
                # product.save()
                products_for_update.append(product)
            Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])

    # bulk edition
    def delete_attributes(self):
        for category in Category.objects.filter(related_groups__group=self.group).only('id'):
            category_id = str(category.id)
            group_id = str(self.group_id)
            atr_id = str(self.attribute_id)
            products_for_update = []
            for product in Product.objects.filter(related_categories__category__related_groups__group=self.group).only(
                    'parameters', 'parameters_structure'):
                (groups := product.parameters_structure[category_id]['groups_attributes'])[group_id]['attributes']. \
                    pop(atr_id)
                if not groups[group_id]['attributes']:
                    groups.pop(group_id)
                if not groups:
                    product.parameters_structure.pop(category_id)
                product.parameters.pop(f'{group_id}-{atr_id}')
                products_for_update.append(product)
            Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])

    # bulk edition
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.old_attribute and self.old_attribute != self.attribute:
            for category in Category.objects.filter(related_groups__group=self.group_id):
                products_for_update = []
                for product in Product.objects.filter(related_categories__category=category.id).only(
                        'parameters', "parameters_structure"):
                    product.parameters_structure[str(category.id)]['groups_attributes'][str(self.group_id)][
                        'attributes'].pop(str(self.old_attribute))
                    product.parameters.pop(f'{self.group.id}-{self.old_attribute}')
                    products_for_update.append(product)
                Product.objects.bulk_update(products_for_update, ['parameters_structure', 'parameters'])
        self.create_attributes()

    def delete(self, *args, **kwargs):
        self.delete_attributes()
        super().delete(*args, **kwargs)


class CategoryCollection(models.Model):
    category_list = TreeManyToManyField('Category', blank=True, default=None, verbose_name='Список категорий', )
    # additional_id = models.CharField(max_length=128, blank=True, null=True, default=None, unique=True,
    # verbose_name='Дополнительный id')
    is_active_custom_order_group = models.BooleanField(default=True,
                                                       verbose_name='Применить индивидуальный порядок групп атрибутов')
    is_active_custom_order_shot_parameters = models.BooleanField(default=True,
                                                                 verbose_name='Применить индивидуальный порядок '
                                                                              'кратких характеристик')
    is_active_custom_order_mini_parameters = models.BooleanField(default=True,
                                                                 verbose_name='Применить индивидуальный порядок мини '
                                                                              'характеристик')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        old_group_list = set(ItemOfCustomOrderGroup.objects.filter(category_collection=self).values_list(
            'group_id', flat=True))
        if self.id:
            new_group_list = set(map(lambda x: x.id, AttrGroup.objects.filter(
                related_categories__category__in=self.category_list.all())))
        else:
            new_group_list = set()
        if not old_group_list == new_group_list:
            del_group_id = old_group_list - new_group_list
            ItemOfCustomOrderGroup.objects.filter(group_id__in=del_group_id, category_collection=self).delete()

    class Meta:
        verbose_name = "Набор категорий с индивидуальным порядком групп атрибутов"
        verbose_name_plural = "Наборы категорий с индивидуальным порядком групп атрибутов"

    def __str__(self):
        if self.category_list.exists():
            return " / ".join(map(str, self.category_list.all().order_by('id').order_by('mptt_level')))
        else:
            return ""

    def update_group_in_product(self):
        Product.objects.filter(category_collection_id=self.id).update(custom_order_group=list(
            map(lambda x: [x[0], x[1]], self.rel_group_iocog.order_by('position').values_list('category', 'group'))))


class ItemOfCustomOrderGroup(models.Model):
    group = models.ForeignKey(AttrGroup, blank=True, null=True, on_delete=models.CASCADE,
                              verbose_name='Группа атрибутов', related_name='rel_cat_collection_iocog')
    category_collection = models.ForeignKey('CategoryCollection', on_delete=models.CASCADE,
                                            verbose_name='Набор категорий', related_name='rel_group_iocog')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    position = models.PositiveIntegerField("Position", null=True, blank=True, default=0)

    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория')

    class Meta:
        verbose_name = "Группа атрибутов набора категорий товаров"
        verbose_name_plural = "Группы атрибутов набора категорий товаров"

    def __str__(self):
        return self.group.name

    def self_attributes_links(self):
        return self.group.self_attributes_links

    self_attributes_links.short_description = 'Содержит атрибуты'

    def getlink_group(self):
        return self.group.getlink

    getlink_group.short_description = 'Группа атрибутов'
    self_attributes_links = property(self_attributes_links)


class ShotParametersOfProduct(models.Model):
    attribute = models.ForeignKey(AttributesInGroup, on_delete=models.CASCADE,
                                  verbose_name='Атрибут для отображения в кратких характеристиках')
    category = TreeForeignKey('Category', blank=True, null=True, default=None, on_delete=models.CASCADE,
                              verbose_name='Категория', related_name='related_shot_attributes')
    name = models.CharField(max_length=128, blank=True, null=True, default='', unique=True, db_index=True,
                            verbose_name='Название для кратких характеристик (оставить пустым если названиие атрибута '
                                         'желаете оставить тем же)')
    is_active = models.BooleanField(default=True, verbose_name='Отображать в кратких характеристиках товара')

    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        verbose_name = "Атрибут для отображения в блоке кратких характеристик товаров"
        verbose_name_plural = "Блок кратких характеристик товаров"
        ordering = ('position',)

    def __str__(self):
        if self.name:
            return f' - {self.name}'
        else:
            return f' - {self.attribute.attribute.name}'


class MiniParametersOfProduct(models.Model):
    attribute = models.ForeignKey(AttributesInGroup, blank=True, null=True, on_delete=models.CASCADE,
                                  verbose_name='Атрибут для отображения в мини характеристиках')
    category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.CASCADE,
                              verbose_name='Категория', related_name='related_mini_attributes')
    name = models.CharField(max_length=128, blank=True, null=True, default='', unique=True, db_index=True,
                            verbose_name='Название для атрибута в выдаче товаров (оставить пустым если названиие '
                                         'атрибута желаете оставить тем же)')
    is_active = models.BooleanField(default=True, verbose_name='Отображать в мини характеристиках товара')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        verbose_name = "Атрибут для отображения в выдаче товаров"
        verbose_name_plural = "Блок хар-к для выдачи товаров"
        ordering = ('position',)

    def __str__(self):
        if self.name:
            return f' - {self.name}'
        else:
            return f' - {self.attribute.attribute.name}'


class SomeSites(models.Model):
    ROLE = (
        (1, " Покупатель "),
        (2, " Поставщик "),
        (3, " Конкурент "),
    )
    name = models.CharField(max_length=128, default=None, unique=True, verbose_name='Название магазина')
    role = models.SmallIntegerField(choices=ROLE)
    info = models.CharField(max_length=128, blank=True, default=None, verbose_name='Краткое описание')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на сайт)')

    class Meta:
        verbose_name = "Сторонний сайт"
        verbose_name_plural = "Сторонние сайты"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class PricesOtherShop(models.Model):
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар')
    shop = models.ForeignKey('SomeSites', blank=True, null=True, default=None, on_delete=models.CASCADE,
                             verbose_name='Магазин')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на товар)')
    info = models.CharField(max_length=128, blank=True, null=True, default=None,
                            verbose_name='Краткое описание)')

    class Meta:
        verbose_name = "Цена конкурента"
        verbose_name_plural = "Цены конкурентов"

    def __str__(self):
        return f"цена магазина {self.shop.name}"
