# from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Category, AttrGroup, CategoryCollection, AttributesInGroup


class CategoryInProductFormActions:
    """docstring for CategoryInProductFormActions"""

    def __init__(self):
        self.instance = self.instance
        self.can_delete = self.can_delete
        self.forms = self.forms

    def group_duplicate_check(self):
        print("RUN DUPLICATE CHECK")
        list_of_query_groups = []
        coincidences_list = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
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
        print("RUN DEL ATR")
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
        print("RUN UPDATE ATR")
        # если категория добавлена
        # отладочный фрагмент
        if form_line.initial == {}:
            self.instance.description += ('Добавлена категория "%s" <br>' % form_line.cleaned_data['category'])

            category = form_line.cleaned_data['category']
            category_id = str(category.id)
            # добаввление мини-характеристик
            mini_attributes = category.related_mini_attributes.all()
            if mini_attributes.exists():
                attributes = dict(list(map(lambda x:
                                           (str(AttributesInGroup.objects.get(id=x[1]).attribute_id),
                                            dict(pos_atr=x[0],
                                                 full_id='%s-%s' % (
                                                     AttributesInGroup.objects.get(id=x[1]).group_id,
                                                     AttributesInGroup.objects.get(id=x[1]).attribute_id),
                                                 name=x[2] if x[2] not in [None, {}] else AttributesInGroup.objects.get(
                                                     id=x[1]).attribute.name,
                                                 value={},
                                                 id=AttributesInGroup.objects.get(id=x[1]).attribute_id)),
                                           mini_attributes.values_list('position', 'attribute', 'name', ))))

                self.instance.mini_parameters_structure[category_id] = {
                    'cat_position': form_line.cleaned_data['position_category'], 'shot_attributes': attributes}

            # добаввление кратких-характеристик
            shot_attributes = category.related_shot_attributes.all()
            if shot_attributes.exists():
                attributes = dict(list(map(lambda x:
                                           (str(AttributesInGroup.objects.get(id=x[1]).attribute_id),
                                            dict(pos_atr=x[0],
                                                 full_id='%s-%s' % (
                                                     AttributesInGroup.objects.get(id=x[1]).group_id,
                                                     AttributesInGroup.objects.get(id=x[1]).attribute_id),
                                                 name=x[2],
                                                 id=AttributesInGroup.objects.get(id=x[1]).attribute_id)),
                                           shot_attributes.values_list('position', 'attribute', 'name', ))))

                self.instance.shot_parameters_structure[category_id] = {
                    'cat_position': form_line.cleaned_data['position_category'], 'shot_attributes': attributes}

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
        print("RUN ADD CC")
        print(category_set)
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
