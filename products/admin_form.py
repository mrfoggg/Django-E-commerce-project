from django import forms
from django.db.models import Count
from django.forms import HiddenInput, NumberInput, TextInput

from .models import *
from .services import CategoryInProductFormActions, get_and_save_product_pos_in_cat, update_addict_attr_values


class ProductAttributesWidget(forms.MultiWidget):
    template_name = "products/product_attribute_widget.html"

    def __init__(self, widgets=[], keys_atr=None):
        self.keys = keys_atr
        super(ProductAttributesWidget, self).__init__(widgets)

    def decompress(self, value):
        return list(map(lambda x: value[x], self.keys)) if value else {}


class ProductAttributesField(forms.MultiValueField):
    def __init__(self, instance, *args, **kwargs):
        list_fields = []
        list_widgets = []
        self.list_keys_attribute = []

        if instance:
            self.list_group_labels = []

            if instance.custom_order_group != [] and instance.is_active_custom_order_group:
                mode = 'custom'
            else:
                mode = 'standart'

            group_items_list = []

            group_id_list = []
            atr_id_set = set()

            parameters_structure = instance.parameters_structure
            custom_order_group = instance.custom_order_group

            def get_attribute_id(attr_it):
                sorted_list_of_attribute_id_with_position = sorted(
                    map(lambda x: [x[1]['atr_position'], x[0]], attr_it))
                srtd_list_of_attribute_id = map(lambda x: int(x[1]), sorted_list_of_attribute_id_with_position)
                return list(srtd_list_of_attribute_id)

            # получаем список group_items_list из элементов: id категории, id группы, упорядоченый список из id
            # атрибутов а так же множество atr_id_set всех id атрибутов для дальнейшего получения словаря
            # attribute_parameters_dict { id atr: { 'name':___, 'type_of_value':____, 'value_list':____}}
            if mode == 'custom':
                for category_and_group in custom_order_group:
                    category_id = category_and_group[0]
                    group_id = category_and_group[1]
                    attribute_items = parameters_structure[str(category_id)]['groups_attributes'][str(group_id)][
                        'attributes'].items()
                    sorted_list_of_attribute_id = get_attribute_id(attribute_items)
                    group_item = [category_id, group_id, sorted_list_of_attribute_id]
                    group_items_list.append(group_item)
                    group_id_list.append(group_id)
                    atr_id_set.update(sorted_list_of_attribute_id)

            if mode == "standart":
                category_list = map(lambda x: [x[1]['cat_position'], int(x[0]), x[1]['groups_attributes']],
                                    parameters_structure.items())
                for category in sorted(category_list):
                    group_list = map(lambda y: [y[1]['group_position'], int(y[0]), y[1]['attributes']],
                                     category[2].items())
                    for group in sorted(group_list):
                        attribute_items = group[2].items()
                        sorted_list_of_attribute_id = get_attribute_id(attribute_items)
                        group_item = [category[1], group[1], sorted_list_of_attribute_id]
                        group_items_list.append(group_item)
                        group_id_list.append(group[1])
                        atr_id_set.update(sorted_list_of_attribute_id)

            # получаем словарь category_names_dict где ключ элемнета это id категории а значение это имя категории
            categories_id_list = map(lambda x: int(x), parameters_structure.keys())
            category_names_dict = {}
            categories_data_list = Category.objects.filter(id__in=categories_id_list).values_list('id', 'name')
            for id_and_name in categories_data_list:
                name = id_and_name[1]
                link = reverse('admin:products_category_change', args=(id_and_name[0],))
                category_names_dict[id_and_name[0]] = mark_safe("<a href={}>{}</a>".format(link, name))

            # получаем словарь group_names_dict где ключ элемента это id группы а значение это имя группы
            # (в данном случае со ссылкой на группу)
            group_names_dict = {}
            group_data_list = AttrGroup.objects.filter(id__in=group_id_list).values_list('id', 'name')
            for id_and_name in group_data_list:
                name = id_and_name[1]
                link = reverse('admin:products_attrgroup_change', args=(id_and_name[0],))
                group_names_dict[id_and_name[0]] = mark_safe("<a href={}>{}</a>".format(link, name))

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
                group_item[0] = category_names_dict[group_item[0]]
                group_item[1] = [group_item[1], group_names_dict[group_item[1]]]
                atr_dict = {}
                for atr_id in group_item[2]:
                    atr_dict[atr_id] = attribute_parameters_dict[atr_id]
                group_item[2] = atr_dict

            for group_items in group_items_list:
                cat_name = group_items[0]
                group_id = group_items[1][0]
                group_name = group_items[1][1]
                atr_count = 0
                for atr_id_str, atr_data in group_items[2].items():
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

                    elif atr_type == 6:
                        ch = list(atr_variants.values_list('id', 'name'))
                        field = forms.MultipleChoiceField(choices=ch, required=False)

                    list_fields.append(field)
                    field.widget.attrs.update({'label': atr_name})
                    if len(group_items[2]) - atr_count == 0:
                        field.widget.attrs.update({'group_end': 'yes'})
                    else:
                        field.widget.attrs.update({'group_end': 'no'})
                    if atr_count == 1:
                        field.widget.attrs.update(
                            {'group_begin': 'yes', 'group_name': group_name, 'category_name': cat_name})
                    else:
                        field.widget.attrs.update({'group_begin': 'no'})
                    list_widgets.append(field.widget)
                    self.list_keys_attribute.append("%s-%s" % (group_id, atr_id))

        self.widget = ProductAttributesWidget(widgets=list_widgets, keys_atr=self.list_keys_attribute)
        super(ProductAttributesField, self).__init__(fields=list_fields, required=False, require_all_fields=False,
                                                     label='', *args, **kwargs)

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
                products = Product.objects.filter(related_categories__category=form.cleaned_data['category'])
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
                    'Ошибка, невозможно добавить группу атрибутов в указаные категории так как она будет дублировать '
                    'в товарах: "%s"' % ', '.join(
                        map(lambda x: x.name, coincidences_list)))


class CategoryForProductInLineFormSet(forms.models.BaseInlineFormSet, CategoryInProductFormActions):
    def clean(self):
        super().clean()
        self.instance.description = ''
        if self.has_changed():
            total_form_count = self.total_form_count()
            total_deleted_forms = len(self.deleted_forms)
            not_should_delete_forms_more_than_one = total_form_count - total_deleted_forms > 1
            if not_should_delete_forms_more_than_one:
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
                    if not (iocog := ItemOfCustomOrderGroup.objects.filter(group_id=group.id,
                                                                           category_collection_id=self.instance.id,
                                                                           category_id=cat_id)).exists():
                        list_for_create_items.append(iocog)
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
