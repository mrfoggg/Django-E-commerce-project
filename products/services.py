from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.utils.safestring import mark_safe

from .models import (AttrGroup, Attribute, AttributesInGroup, AttributeValue, CategoryCollection, ProductInCategory)


def get_and_save_product_pos_in_cat(form, position):
    product_in_cat_item = form.save(commit=False)
    product_in_cat_item.position_product = position
    product_in_cat_item.save()
    print(f'product_id: {product_in_cat_item.id}')
    print(f'product_position: {product_in_cat_item.position_product}')


def reformat_addict_attr_for_admin(attrs_sorted):
    parameters_display = [
        '<br>'.join(
            [
                '%s-%s' % (
                    attr_data.name,
                    ', '.join(attr_data.value_str) if isinstance(attr_data.value_str, list) else attr_data.value_str
                )
                for attr_data in cat[1]
            ])  # категория без порядкового номера
        for cat in attrs_sorted]  # отсортированый перечень категорий
    return mark_safe('<br>'.join(parameters_display))


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
    def delete_attributes(product, category):
        product.description += f'Удалена категория {category} <br>'
        category_id = str(category.id)
        if category_id in product.shot_parameters_structure.keys():
            product.shot_parameters_structure.pop(category_id)
        if category_id in product.mini_parameters_structure.keys():
            product.mini_parameters_structure.pop(category_id)
        if str(category.id) in product.parameters_structure.keys():
            product.parameters_structure.pop(str(category.id))

        for group_id in AttrGroup.objects.filter(related_categories__category=category.id).values_list('id', flat=True):
            for atr in Attribute.objects.filter(related_groups__group=group_id).only('id'):
                atr_id = str(atr.id)
                if (full_id := f'{group_id}-{atr_id}') in product.parameters:
                    product.parameters.pop(full_id)

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
            product.shot_parameters_structure[category_id] = {
                'cat_position': position_category, 'attributes':
                    build_custom_attributes_structure_field_data(this_category_shot_attributes)}

        this_category_mini_attributes = category.related_mini_attributes.all()
        if this_category_mini_attributes.exists():
            product.mini_parameters_structure[category_id] = {
                'cat_position': position_category, 'attributes':
                    build_custom_attributes_structure_field_data(this_category_mini_attributes)}
        next_position = 0 if (max_pos := product_in_cat_qs['position_product__max']) is None else max_pos + 1
        return next_position

    @staticmethod
    def reorder_attributes(product, category_id, new_category_order):
        print('RUN reorder')
        if (cat_id := str(category_id)) in product.shot_parameters_structure.keys():
            product.shot_parameters_structure[cat_id]["cat_position"] = new_category_order
        if cat_id in product.mini_parameters_structure.keys():
            product.mini_parameters_structure[cat_id]["cat_position"] = new_category_order

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
