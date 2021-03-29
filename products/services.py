import copy
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Max, Subquery, OuterRef, Q, Prefetch
from django.utils.safestring import mark_safe
from collections import namedtuple
from .models import (AttrGroup, Attribute, AttributesInGroup, AttributeValue, Category, CategoryCollection, Product,
                     ProductInCategory, ItemOfCustomOrderGroup, ItemOfCustomOrderShotParameters,
                     ItemOfCustomOrderMiniParameters, AttrGroupInCategory)


def remove_attr_data_from_products(product=None, category=None, attr_group=None, attr=None):
    mode = None
    list_of_deleted_collections, list_of_modified_collections, replaced_collection_dict = [], [], {}
    if category and not (product or attr_group or attr):
        mode = 'delete_category'
    if mode == 'delete_category':
        for collection in CategoryCollection.objects.annotate(cat_id_list=ArrayAgg('category_list')).filter(
                category_list=category):
            # удаляем коллекцию если остается одна категория, сохранеяем ее в списке удаленных чтобы в связанных товарах
            # custom_order_group сделать пустым
            if len(collection.cat_id_list) == 2:
                list_of_deleted_collections.append(collection.id)
                collection.delete()
            else:
                # находим коллекции которые совпадают с этой укороченной
                other_collection = CategoryCollection.objects.annotate(cnt=Count('category_list')).filter(
                    cnt=len(collection.cat_id_list) - 1).exclude(id=collection.id)
                for cat in collection.cat_id_list:
                    if cat == category.id:
                        continue
                    other_collection = other_collection.filter(category_list=cat)
                # помечаем эту коллекцию на удаление и в replaced_collection_dict записываем id коллекции
                # на какую ее поменять для свазанных товаров (и с какой взять custom_order_group
                if other_collection.exists():
                    replaced_collection_dict[collection.id] = other_collection[0].id
                    # collection.delete()
                else:
                    # если коллекцию не удалили то помечаем ее как модифицированую чтобы для связаных товаров
                    # обновить custom_order_group согласно изменений в коллекции
                    list_of_modified_collections.append(collection.id)
        print(list_of_deleted_collections)
        print(replaced_collection_dict)
        print(list_of_modified_collections)

    if product:
        products_list = [product]
    else:
        products_list = Product.objects.filter(
            related_categories__category=category).only(
            'parameters', 'parameters_structure', 'shot_parameters_structure', 'mini_parameters_structure')
    all_data_products_to_update_type = namedtuple('all_data_products_to_update_type', 'products_list fields_names_list')
    all_data_products_to_update = all_data_products_to_update_type([], [])
    for product in products_list:
        if (category_id := str(category.id)) in product.parameters_structure.keys():
            product.parameters_structure.pop(category_id)
            all_data_products_to_update.fields_names_list.append('parameters_structure')
            all_data_products_to_update.fields_names_list.append('parameters')
        if category_id in product.shot_parameters_structure.keys():
            product.shot_parameters_structure.pop(category_id)
            all_data_products_to_update.fields_names_list.append('shot_parameters_structure')
        if category_id in product.mini_parameters_structure.keys():
            product.mini_parameters_structure.pop(category_id)
            all_data_products_to_update.fields_names_list.append('mini_parameters_structure')
        if mode == 'delete_category':
            if product.category_collection_id in list_of_deleted_collections:
                product.custom_order_group = []
            if product.category_collection_id in replaced_collection_dict:
                print(
                    f'коллекция {product.category_collection_id} заменена на {replaced_collection_dict[product.category_collection_id]}')
                product.category_collection_id = replaced_collection_dict[product.category_collection_id]
                product.custom_order_group = [
                    [gr.category_id, gr.group_id] for gr in CategoryCollection.objects.get(
                        id=product.category_collection_id).rel_group_iocog.order_by('position')]
                all_data_products_to_update.fields_names_list.append('custom_order_group')
                all_data_products_to_update.fields_names_list.append('category_collection')
        if mode == 'delete_category' or mode == 'delete_group':
            if product.category_collection_id in list_of_modified_collections:
                # в custom_order_group удаляем отдельные элементы
                for i, cat_and_group in enumerate(product.custom_order_group):
                    if mode == 'delete_category':
                        if cat_and_group[0] == category.id:
                            product.custom_order_group[i].pop()
                            all_data_products_to_update.fields_names_list.append('custom_order_group')
                    if mode == 'delete_group':
                        if cat_and_group[1] == attr_group.id:
                            product.custom_order_group[i].pop()
                            all_data_products_to_update.fields_names_list.append('custom_order_group')
        # select_related
        for group_id in AttrGroup.objects.filter(related_categories__category=category).values_list('id', flat=True):
            for atr_id in Attribute.objects.filter(related_groups__group=group_id).values_list('id', flat=True):
                if (full_id := f'{group_id}-{atr_id}') in product.parameters:
                    product.parameters.pop(full_id)
        all_data_products_to_update.products_list.append(product)
    # удалить замененные коллекции
    CategoryCollection.objects.filter(id__in=replaced_collection_dict).delete()
    return all_data_products_to_update


def save_and_make_copy(obj, model_to_copy):
    obj.save()
    obj_copy = copy.copy(obj)
    obj_copy.id = None
    obj_copy.slug = None
    copies = [0]
    for atr in model_to_copy.objects.filter(name__startswith=obj.name + ' (@копия #'):
        left_part_name = atr.name[(atr.name.find(' (@копия #') + 10):]
        number_of_copy = int(left_part_name[:left_part_name.find(')')])
        copies.append(number_of_copy)
    obj_copy.name = obj.name + ' (@копия #%s)' % (max(copies) + 1)
    return obj_copy


def get_related_objects_list_copies(related_objects, related_field_name, obj_copy):
    related_objects_copies_list = []
    for related_objects_item in related_objects:
        copy_related_objects_item = copy.copy(related_objects_item)
        copy_related_objects_item.id = None
        copy_related_objects_item.__dict__[related_field_name] = obj_copy
        related_objects_copies_list.append(copy_related_objects_item)
    return related_objects_copies_list


def get_and_save_product_pos_in_cat(form, position):
    product_in_cat_item = form.save(commit=False)
    product_in_cat_item.position_product = position


def update_addict_attr_values(prod, new_param):
    shot_atr_field = prod.shot_parameters_structure
    mini_atr_field = prod.mini_parameters_structure

    def update(field, param):
        for cat in field.values():
            for atr_full_id, atr in cat['attributes'].items():
                type_val = Attribute.objects.get(pk=atr['id']).type_of_value
                val = param[atr_full_id]
                atr['value'] = val
                if type_val == 5 and val != '':
                    atr['value_str'] = AttributeValue.objects.get(pk=int(val)).name
                elif type_val == 6 and val != []:
                    atr['value_str'] = list(AttributeValue.objects.filter(
                        pk__in=list(map(
                            int,
                            val
                        ))
                    ).values_list('name', flat=True))
                else:
                    atr['value_str'] = val

    update(shot_atr_field, new_param)
    update(mini_atr_field, new_param)


class CategoryInProductFormActions:
    """mixin for CategoryForProductInLineFormSet"""

    def __init__(self):
        # self.instance = self.instance
        self.can_delete = self.can_delete
        self.forms = self.forms

    def group_duplicate_check(self):
        categories = []
        list_of_query_groups = []
        coincidences_list = set()
        for form in self.forms:
            if 'category' not in form.cleaned_data:
                raise ValidationError('Вы пытаетесь добавить несуществующую категорию')
            if self.can_delete and self._should_delete_form(form):
                continue
            category = form.cleaned_data['category']
            if category in categories:
                raise ValidationError(f"Категория {category} дублируется")
            categories.append(category)
            groups = AttrGroup.objects.filter(related_categories__category=form.cleaned_data['category'])
            list_of_query_groups.append(groups)

        i = 0
        for query_1_groups in list_of_query_groups:
            j = 0
            for query_2_groups in list_of_query_groups:
                if j == i:
                    j += 1
                    continue
                coincidences = query_1_groups.intersection(query_2_groups)
                if coincidences.exists():
                    coincidences_list.update(coincidences)
                j += 1
            i += 1
            if i == len(list_of_query_groups):
                break
        if coincidences_list:
            raise ValidationError('Ошибка, в категориях дублируются группы атрибутов: "%s"' % mark_safe(
                ', '.join(map(lambda x: x.name, coincidences_list))))

    @staticmethod
    def add_attributes(product, category, position_category):
        category_id = str(category.id)
        product.description += f'Добавлена категория {category} <br>'

        product_in_cat_qs = ProductInCategory.objects.filter(category_id=category_id).aggregate(
            Max('position_product'))

        if category.related_groups.filter(group__related_attributes__isnull=False):
            product.parameters_structure |= {category_id: {'cat_position': position_category, 'groups_attributes': {}}}
            for group_in_cat in category.related_groups.filter(group__related_attributes__isnull=False).select_related(
                    'group'):
                group_id = str(group_in_cat.group_id)
                product.parameters_structure[category_id]['groups_attributes'] |= {
                    group_id: {'group_position': group_in_cat.position, 'attributes': {}}}
                for atr_group in group_in_cat.group.related_attributes.select_related('attribute').all():
                    product.parameters_structure[category_id]['groups_attributes'][group_id]['attributes'] |= {
                        (attr_id := str(atr_group.attribute_id)): {'atr_position': atr_group.position}
                    }
                    product.parameters |= {f'{group_id}-{attr_id}': None}

        def build_custom_attributes_structure_field_data(attributes_query):
            attribute_structure = dict([
                ('%s-%s' % (
                    AttributesInGroup.objects.get(id=x.attribute).group_id,
                    AttributesInGroup.objects.get(id=x.attribute).attribute_id
                ),
                 dict(
                     pos_atr=x.position,
                     name=x.name if x.name else AttributesInGroup.objects.get(id=x.attribute).attribute.name,
                     # name=x.name if x.name not in [None, {}] else '',
                     id=AttributesInGroup.objects.get(id=x.attribute).attribute_id,
                     value_str='не указано',
                     value=''
                 ))
                for x in attributes_query.values_list('position', 'attribute', 'name', named=True)])
            return attribute_structure

        this_category_shot_attributes = category.related_shot_attributes.all()
        if this_category_shot_attributes.exists():
            product.shot_parameters_structure |= {category_id: {
                'cat_position': position_category, 'attributes':
                    build_custom_attributes_structure_field_data(this_category_shot_attributes)}}

        this_category_mini_attributes = category.related_mini_attributes.all()
        if this_category_mini_attributes.exists():
            product.mini_parameters_structure |= {category_id: {
                'cat_position': position_category, 'attributes':
                    build_custom_attributes_structure_field_data(this_category_mini_attributes)}}
        next_position = 0 if (max_pos := product_in_cat_qs['position_product__max']) is None else max_pos + 1
        return next_position if product else 'all_data_products_to_update'

    @staticmethod
    def reorder_attributes(product, category_id, new_category_order):
        if (cat_id := str(category_id)) in product.shot_parameters_structure.keys():
            product.shot_parameters_structure[cat_id]["cat_position"] = new_category_order
        if cat_id in product.mini_parameters_structure.keys():
            product.mini_parameters_structure[cat_id]["cat_position"] = new_category_order
        if cat_id in product.parameters_structure.keys():
            product.parameters_structure[cat_id]["cat_position"] = new_category_order

    @staticmethod
    def add_category_collection(product, category_set):
        print(f'RUN add_category_collection with category_set: {category_set}')
        # выбираем коллекции нужной длины
        category_collection = CategoryCollection.objects.annotate(cnt=Count('category_list')).filter(
            cnt=len(category_set))
        # последовательно отбираем только те коллекции которые содержат каждую из категорий размещения
        for cat in category_set:
            category_collection = category_collection.filter(category_list=cat).values_list('id', flat=True)
        if category_collection.exists():
            category_collection_id = category_collection[0]
            product.custom_order_group = [[gr.category_id, gr.group_id] for gr in CategoryCollection.objects.get(
                id=category_collection_id).rel_group_iocog.order_by('position')]
            product.category_collection_id = category_collection_id
        else:
            product.category_collection_id = None
            product.custom_order_group = []

    def _should_delete_form(self, form):
        self._should_delete_form(form)


def add_items(collection_id, cat_id_list, max_group=0, max_mini=0, max_shot=0):
    iocog_create_list = []
    ioshot_create_list = []
    iomini_create_list = []
    not_empty_groups = Prefetch('related_groups',
                                queryset=AttrGroupInCategory.objects.exclude(group__related_attributes=None),
                                to_attr='groups_with_position')
    categories = Category.objects.filter(id__in=cat_id_list).only('id').prefetch_related(
        not_empty_groups, 'related_shot_attributes', 'related_mini_attributes').annotate(
        max_group_position=Max('related_groups__position'),
        max_shot_position=Max('related_shot_attributes__position'),
        max_mini_position=Max('related_mini_attributes__position')
    )

    for cat in categories:
        for group in cat.groups_with_position:
            iocog_create_list.append(ItemOfCustomOrderGroup(
                group_id=group.group_id, category_collection_id=collection_id, category_id=cat.id,
                position=max_group + group.position
            ))
        max_group += cat.max_group_position + 1
        for shot_attr in cat.related_shot_attributes.all():
            ioshot_create_list.append(ItemOfCustomOrderShotParameters(
                attribute=shot_attr, category_collection_id=collection_id, category_id=cat.id,
                position=max_shot + shot_attr.position
            ))
        max_shot += cat.max_shot_position + 1
        for mini_attr in cat.related_mini_attributes.all():
            iomini_create_list.append(ItemOfCustomOrderMiniParameters(
                attribute=mini_attr, category_collection_id=collection_id, category_id=cat.id,
                position=max_mini + mini_attr.position
            ))
        max_mini += cat.max_mini_position + 1

    ItemOfCustomOrderGroup.objects.bulk_create(iocog_create_list)
    ItemOfCustomOrderShotParameters.objects.bulk_create(ioshot_create_list)
