from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Category, AttrGroup, CategoryCollection, AttributesInGroup, Attribute, AttributeValue


def update_addict_attr(prod, new_param):
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
    """docstring for CategoryInProductFormActions"""

    def __init__(self):
        self.instance = self.instance
        self.can_delete = self.can_delete
        self.forms = self.forms

    def group_duplicate_check(self):
        list_of_query_groups = []
        coincidences_list = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                print('SHOULD_DELETE')
                continue
            print(form.cleaned_data['category'])
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
        if coincidences_list:
            raise ValidationError('Ошибка, в категориях дублируются группы атрибутов: "%s"' % mark_safe(
                ', '.join(map(lambda x: x.name, coincidences_list))))

    def delete_attributes(self, category):
        self.instance.description += 'Удалена категория %s <br>' % category
        category_id = str(category.id)
        if category_id in self.instance.shot_parameters_structure.keys():
            self.instance.shot_parameters_structure.pop(category_id)
        if category_id in self.instance.mini_parameters_structure.keys():
            self.instance.mini_parameters_structure.pop(category_id)
        # if str(category.id) in self.instance.parameters_structure.keys():
        #     self.product.parameters_structure.pop(str(category.id))
        #
        # for group in AttrGroup.objects.filter(related_categories__category=category.id).only('id'):
        #     group_id = str(group.id)
        #     for atr in Attribute.objects.filter(related_groups__group=group_id).only('id'):
        #         atr_id = str(atr.id)
        #         if '%s-%s' % (group_id, atr_id) in self.product.parameters:
        #             self.product.parameters.pop('%s-%s' % (group_id, atr_id))

    def update_attributes(self, form_line):
        # если категория добавлена
        # отладочный фрагмент
        if form_line.initial == {}:
            self.instance.description += ('Добавлена категория "%s" <br>' % form_line.cleaned_data['category'])

            category = form_line.cleaned_data['category']
            category_id = str(category.id)

            def build_attribute_dict(attributes_query):
                attributes = dict(list(map(
                    lambda x:
                    ('%s-%s' % (
                        AttributesInGroup.objects.get(id=x.attribute).group_id,
                        AttributesInGroup.objects.get(id=x.attribute).attribute_id),
                     dict(pos_atr=x.position,
                          name=x.name if x.name else AttributesInGroup.objects.get(id=x.attribute).attribute.name,
                          # name=x.name if x.name not in [None, {}] else '',
                          id=AttributesInGroup.objects.get(id=x.attribute).attribute_id,
                          value_str='не указано',
                          value=''
                          )),
                    attributes_query.values_list('position', 'attribute', 'name', named=True))))
                return attributes

            # добавление кратких-характеристик
            shot_attributes = category.related_shot_attributes.all()
            if shot_attributes.exists():
                self.instance.shot_parameters_structure[category_id] = {
                    'cat_position': form_line.cleaned_data['position_category'], 'attributes':
                        build_attribute_dict(shot_attributes)}

            # добавление мини-характеристик
            mini_attributes = category.related_mini_attributes.all()
            if mini_attributes.exists():
                self.instance.mini_parameters_structure[category_id] = {
                    'cat_position': form_line.cleaned_data['position_category'], 'attributes':
                        build_attribute_dict(mini_attributes)}

        # если категория изменена
        elif 'category' in form_line.changed_data:
            old_category = Category.objects.get(id=form_line.initial['category'])
            new_category = form_line.cleaned_data['category']
            self.instance.description += 'Категория "%s" изменена на "%s" <br>' % (
                old_category, new_category)
        # если только изменен порядок следования категорий
        else:
            self.instance.description += "Изменен порядок категории %s на %s <br>" % (
                form_line.cleaned_data['category'], form_line.cleaned_data['position_category']
            )

    def add_category_collection(self, category_set):
        # выбираем коллекции нужной длины
        category_collection = CategoryCollection.objects.annotate(cnt=Count('category_list')).filter(
            cnt=len(category_set))
        # последовательно отбираем только те коллекции котрые содержат каждую из категор ия
        for cat in category_set:
            category_collection = category_collection.filter(category_list=cat).values_list('id')

        if category_collection.exists():
            category_collection_id = category_collection[0][0]
            custom_order_group = map(lambda x: [x.category_id, x.group_id], CategoryCollection.objects.get(
                id=category_collection_id).rel_group_iocog.order_by('position'))
            self.instance.category_collection_id = category_collection_id
            self.instance.custom_order_group = list(custom_order_group)
        else:
            self.instance.category_collection_id = None
            self.instance.custom_order_group = []

    def _should_delete_form(self, form):
        self._should_delete_form(form)
