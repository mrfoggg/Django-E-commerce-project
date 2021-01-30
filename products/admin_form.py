from collections import namedtuple
from django import forms
from django.db.models import Count
from django.forms import HiddenInput, NumberInput, TextInput
from operator import attrgetter

from .models import *
from .services import CategoryInProductFormActions, get_and_save_product_pos_in_cat, update_addict_attr_values


class ProductAttributesWidget(forms.MultiWidget):
    template_name = "products/product_attribute_widget.html"

    def __init__(self, widgets=None, keys_atr=None):
        self.keys = keys_atr
        super(ProductAttributesWidget, self).__init__(widgets)

    def decompress(self, value):
        return [value[x] for x in self.keys] if value else {}


class ProductAttributesField(forms.MultiValueField):
    def __init__(self, instance, **kwargs):
        list_fields = []
        list_widgets = []
        self.list_keys_attribute = []

        if instance:
            # self.list_group_labels = []

            if instance.custom_order_group != [] and instance.is_active_custom_order_group:
                mode = 'custom'
            else:
                mode = 'standart'

            parameters_structure = instance.parameters_structure
            custom_order_group = instance.custom_order_group

            def get_sorted_attribute_id_list(attr_it):
                sorted_list_of_attribute_id_with_position = sorted([[_atr_data['atr_position'], _atr_id]
                                                                    for _atr_id, _atr_data in attr_it.items()])
                return [int(atr_data_wo_pos[1]) for atr_data_wo_pos in sorted_list_of_attribute_id_with_position]

            group_items_list = []
            group_id_list = []
            atr_id_set = set()
            # sorted_group_struct = namedtuple('sorted_group_struct', 'cat_id group_id sorted_atr_id_list')

            if mode == 'custom':
                for category_and_group_id_list in custom_order_group:
                    category_id = category_and_group_id_list[0]
                    group_id = category_and_group_id_list[1]
                    attributes_dict = parameters_structure[str(category_id)]['groups_attributes'][str(group_id)][
                        'attributes']
                    sorted_list_of_attribute_id = get_sorted_attribute_id_list(attributes_dict)
                    group_item = {
                        'cat_id': category_id, 'group_id': group_id, 'sorted_atr_id_list': sorted_list_of_attribute_id}
                    group_items_list.append(group_item)
                    group_id_list.append(group_id)
                    atr_id_set.update(sorted_list_of_attribute_id)

            if mode == "standart":
                struct_with_pos = namedtuple('inner_struct', 'position id inner_elements')
                category_list = [struct_with_pos(cat_data['cat_position'], int(cat_id), cat_data['groups_attributes'])
                                 for cat_id, cat_data in parameters_structure.items()]
                for category in sorted(category_list, key=attrgetter('position')):
                    group_list = [
                        struct_with_pos(group_data['group_position'], int(group_id), group_data['attributes'])
                        for group_id, group_data in category.inner_elements.items()
                    ]
                    for group in sorted(group_list, key=attrgetter('position')):
                        attributes_dict = group.inner_elements
                        sorted_list_of_attribute_id = get_sorted_attribute_id_list(attributes_dict)
                        group_item = {'cat_id': category.id, "group_id": group.id, 'sorted_atr_id_list': sorted_list_of_attribute_id}
                        group_items_list.append(group_item)
                        group_id_list.append(group.id)
                        atr_id_set.update(sorted_list_of_attribute_id)

            # получаем словарь category_names_dict где ключ элемнета это id категории а значение это имя категории
            categories_id_list = [int(id_str) for id_str in parameters_structure.keys()]
            category_names_dict = {
                cat.id: mark_safe(
                    "<a href=%s>%s</a>" % (reverse('admin:products_category_change', args=(cat.id,)), cat.name)
                )
                for cat in Category.objects.filter(id__in=categories_id_list).values_list('id', 'name', named=True)
            }
            for cat_descr in Category.objects.filter(id__in=categories_id_list).values_list('id', 'name', named=True):
                href = reverse('admin:products_category_change', args=(cat_descr.id,))
                category_names_dict[cat_descr.id] = mark_safe(f"<a href={href}>{cat_descr.name}</a>")

            group_names_dict = {
                attr_gr.id: mark_safe(
                    "<a href=%s>%s</a>" % (reverse('admin:products_attrgroup_change', args=(attr_gr.id,)), attr_gr.name)
                )
                for attr_gr in AttrGroup.objects.filter(id__in=group_id_list).values_list('id', 'name', named=True)
            }

            # получаем словарь attribute_parameters_dict где ключ элемента это id атрибута а значение это словарь
            atr_id_list = list(atr_id_set)
            attribute_parameters_dict = {}
            attributes_data_query = Attribute.objects.filter(id__in=atr_id_list).only('id', 'name', 'type_of_value',
                                                                                      'value_list')
            for attribute in attributes_data_query:
                attribute_parameters_dict[attribute.id] = {'name': attribute.name,
                                                           'type_of_value': attribute.type_of_value,
                                                           'value_list': attribute.value_list.all()}

            # перебираем group_items_list из элементов: id категории, id группы, упорядоченый список из
            # id атрибутов нополняем его именами категорий, групп
            for group_item in group_items_list:
                group_item['cat_id'] = category_names_dict[group_item['cat_id']]
                group_item['group_id'] = [group_item['group_id'], group_names_dict[group_item['group_id']]]
                atr_dict = {}
                for atr_id in group_item['sorted_atr_id_list']:
                    atr_dict[atr_id] = attribute_parameters_dict[atr_id]
                group_item['sorted_atr_id_list'] = atr_dict

            for group_items in group_items_list:
                cat_name = group_items['cat_id']
                group_id = group_items['group_id'][0]
                group_name = group_items['group_id'][1]
                atr_count = 0
                for atr_id_str, atr_data in group_items['sorted_atr_id_list'].items():
                    atr_count += 1
                    atr_id = int(atr_id_str)
                    atr_name = atr_data['name']
                    atr_type = atr_data['type_of_value']
                    atr_variants = atr_data['value_list']

                    if atr_type == 1:
                        field = forms.CharField(required=False)
                    elif atr_type == 2:
                        field = forms.IntegerField(required=False)
                    elif atr_type == 3:
                        field = forms.FloatField(required=False)
                    elif atr_type == 4:
                        field = forms.BooleanField(required=False)
                    elif atr_type == 5:
                        ch = list(atr_variants.values_list('id', 'name'))
                        ch.append([None, '--- Выберите значение ---'])
                        field = forms.ChoiceField(choices=ch, required=False)

                    else:
                        ch = list(atr_variants.values_list('id', 'name'))
                        field = forms.MultipleChoiceField(choices=ch, required=False)

                    list_fields.append(field)
                    field.widget.attrs.update({'label': atr_name})
                    if len(group_items['sorted_atr_id_list']) - atr_count == 0:
                        field.widget.attrs.update({'group_end': 'yes'})
                    else:
                        field.widget.attrs.update({'group_end': 'no'})
                    if atr_count == 1:
                        field.widget.attrs.update(
                            {'group_begin': 'yes', 'group_name': group_name, 'category_name': cat_name})
                    else:
                        field.widget.attrs.update({'group_begin': 'no'})
                    list_widgets.append(field.widget)
                    self.list_keys_attribute.append(f"{group_id}-{atr_id}")

        self.widget = ProductAttributesWidget(widgets=list_widgets, keys_atr=self.list_keys_attribute)
        super(ProductAttributesField, self).__init__(fields=list_fields, required=False, require_all_fields=False,
                                                     label='', **kwargs)

    def compress(self, data_list):
        if len(data_list) != 0:
            val = {key: value for key, value in zip(self.list_keys_attribute, data_list)}
        else:
            val = {key: None for key in self.list_keys_attribute}
        return val


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['parameters'] = ProductAttributesField(instance=self.instance)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["parameters_structure"] != self.instance.parameters_structure:
            err = mark_safe('Структура характеристик была изменена: ' + self.instance.get_link_refresh)
            raise forms.ValidationError(err)

        if 'parameters' in self.changed_data:
            update_addict_attr_values(self.instance, cleaned_data['parameters'])

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'parameters_structure': HiddenInput(),
            # 'parameters_structure': JSONEditorWidget,
            'art': TextInput(attrs={'size': 10}),
            'name': TextInput(attrs={'size': 50}),
            'length': NumberInput(attrs={'size': 2}),
            'width': NumberInput(attrs={'size': 5}),
            'height': NumberInput(attrs={'size': 3}),
            'length_box': NumberInput(attrs={'size': 5}),
            'width_box': NumberInput(attrs={'size': 3}),
            'height_box': NumberInput(attrs={'size': 5}),
            'weight': NumberInput(attrs={'size': 5}),
            # 'warranty': NumberInput(attrs={'size':5}),
        }


class CategoriesInGroupInlineFormSet(forms.models.BaseInlineFormSet):
    # хз нужно ли при переходе с грапелли на чистую админку
    def add_fields(self, form, index):
        super(CategoriesInGroupInlineFormSet, self).add_fields(form, index)
        form.fields['position'] = forms.IntegerField(widget=HiddenInput(), initial=0)

    def clean(self):
        super().clean()
        if (self.total_form_count() - len(self.deleted_forms)) > 1:
            list_of_sets_products = []
            coincidences_list = set()
            for form in self.forms:
                products = Product.objects.filter(related_categories__category=form.cleaned_data[
                    'category']).values_list('id', 'name')
                list_of_sets_products.append(products)
            i = 0
            for query_1_of_products in list_of_sets_products:
                j = 0
                for query_2_of_products in list_of_sets_products:
                    if j == i:
                        j += 1
                        continue
                    coincidences = query_1_of_products.intersection(query_2_of_products)
                    if coincidences:
                        coincidences_list.update(coincidences)
                    j += 1
                i += 1
                if i == len(list_of_sets_products):
                    break
            if coincidences_list:
                raise ValidationError(
                    "Ошибка, невозможно добавить группу атрибутов в указаные категории так как она будет дублировать" \
                    + f"в товарах: {', '.join([x[1] for x in coincidences_list])}")


class CategoryForProductInLineFormSet(forms.models.BaseInlineFormSet, CategoryInProductFormActions):
    def clean(self):
        super().clean()
        self.instance.description = ''
        if self.has_changed():
            total_form_count = self.total_form_count()
            if (not_should_delete_forms_more_than_one := total_form_count - len(self.deleted_forms)) > 1:
                self.group_duplicate_check()
            new_category_set = set()
            category_set_changed = False
            for form in self.forms:
                if self.can_delete and self._should_delete_form(form):
                    self.delete_attributes(self.instance, form.cleaned_data['category'])
                    category_set_changed = True
                    continue
                else:
                    if not_should_delete_forms_more_than_one:
                        new_category_set.add(form.cleaned_data['category'].id)
                    if form.has_changed():
                        if form.initial == {}:
                            product_position = self.add_attributes(
                                self.instance, form.cleaned_data["category"], form.cleaned_data["position_category"])
                            get_and_save_product_pos_in_cat(form, product_position)
                            category_set_changed = True

                        else:
                            if 'category' in form.changed_data:
                                print(
                                    f'категория {form.initial["category"]} изменена на {form.cleaned_data["category"].id}')
                                self.delete_attributes(self.instance, Category.objects.get(id=form.initial["category"]))
                                product_position = self.add_attributes(
                                    self.instance, form.cleaned_data["category"],
                                    form.cleaned_data["position_category"])
                                category_set_changed = True
                                get_and_save_product_pos_in_cat(form, product_position)
                            else:
                                self.reorder_attributes(self.instance, form.initial["category"],
                                                        form.cleaned_data["position_category"])

            if not not_should_delete_forms_more_than_one and total_form_count > 1:
                print('delete CC')
                self.instance.category_collection_id = None
                self.instance.custom_order_group = []
            else:
                if (not self.instance.id or category_set_changed) and not_should_delete_forms_more_than_one:
                    self.add_category_collection(self.instance, new_category_set)


class AttrGroupForm(forms.ModelForm):
    class Meta:
        model = AttrGroup
        fields = ('name',)
        widgets = {
            'name': TextInput(attrs={'size': 50}),
        }


class AttributeForm(forms.ModelForm):
    class Meta:
        model = AttrGroup
        fields = ('name',)
        widgets = {
            'name': TextInput(attrs={'size': 50}),
        }


class CategoryCollectionForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        cat_list = cleaned_data['category_list']
        if (len_cat_list := len(cat_list)) < 2:
            raise forms.ValidationError('Коллекция не может состоять менее чем из двух групп')
        cat_list_id_list = cat_list.order_by('mptt_level').values_list('id', flat=True)
        other_same_collection = CategoryCollection.objects.annotate(cnt=Count('category_list')).filter(
            cnt=len_cat_list)

        for cat_id in cat_list_id_list:
            other_same_collection = other_same_collection.filter(category_list__id=cat_id)

        if other_same_collection.exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Такой набор категорий уже определен')

        if self.instance.id:
            for cat_id in cat_list_id_list:
                list_for_create_items = []
                for group in AttrGroup.objects.filter(related_categories__category__id=cat_id).only('id'):
                    if not (ItemOfCustomOrderGroup.objects.filter(group_id=group.id,
                                                                 category_collection_id=self.instance.id,
                                                                 category_id=cat_id)).exists():
                        list_for_create_items.append(
                            ItemOfCustomOrderGroup(group_id=group.id, category_collection_id=self.instance.id,
                                                   category_id=cat_id)
                        )
                ItemOfCustomOrderGroup.objects.bulk_create(list_for_create_items)
            new_set = set(cat_list_id_list)
            old_set = set(Category.objects.filter().values_list('id', flat=True))
            if old_set != new_set:
                Product.objects.filter(category_collection_id=self.instance.id).update(category_collection_id=None,
                                                                                       custom_order_group=[])
        products_add = Product.objects.exclude(category_collection_id=self.instance.id).annotate(
            cnt=Count('related_categories')).filter(cnt=len_cat_list)
        for cat_id in cat_list_id_list:
            products_add = products_add.filter(related_categories__category_id=cat_id)
        products_add.update(category_collection_id=self.instance.id)

    class Meta:
        widgets = {
            'additional_id': TextInput(attrs={'size': 10})
        }


class ItemOfCustomOrderGroupInLineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        custom_order_list = [
            [form.cleaned_data['position'], form.cleaned_data['id'].category_id, form.cleaned_data['id'].group_id]
            for form in self.forms
        ]
        custom_order_list.sort()
        group_list = [x[1:] for x in custom_order_list]
        if self.instance.is_active_custom_order_group:
            Product.objects.filter(category_collection_id=self.instance.id).update(custom_order_group=group_list)
        else:
            Product.objects.filter(category_collection_id=self.instance.id).update(custom_order_group=[])
