# Generated by Django 3.1.7 on 2021-02-21 20:22

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AttrGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=128, null=True, unique=True)),
            ],
            options={
                'verbose_name': 'Группа атрибутов',
                'verbose_name_plural': 'Группы атрибутов',
            },
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('position', models.PositiveIntegerField(blank=True, null=True, verbose_name='Position')),
                ('type_of_value', models.SmallIntegerField(choices=[(1, 'Текст'), (2, 'Целое положит. число'), (3, 'Число'), (4, 'Логический тип'), (5, 'Вариант из фикс. значений'), (6, 'Набор фикс. значений')], default=1, verbose_name='Тип данных')),
            ],
            options={
                'verbose_name': 'Атрибут',
                'verbose_name_plural': 'Атрибуты',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='AttributesInGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(null=True, verbose_name='Position')),
                ('attribute', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_groups', to='products.attribute', verbose_name='Атрибут')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_attributes', to='products.attrgroup', verbose_name='Группа атрибутов')),
            ],
            options={
                'verbose_name': 'Атрибут группы',
                'verbose_name_plural': 'Атрибуты группы',
                'ordering': ['position'],
                'unique_together': {('attribute', 'group')},
            },
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=128, null=True, unique=True)),
            ],
            options={
                'verbose_name': 'Значение атрибутов',
                'verbose_name_plural': 'Значения атрибутов',
            },
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
            ],
            options={
                'verbose_name': 'Торговая марка',
                'verbose_name_plural': 'Торговые марки',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('description', models.TextField(blank=True, default=None, null=True, verbose_name='Описание категории')),
                ('image', models.ImageField(blank=True, null=True, upload_to='category_images/', verbose_name='Фото категории')),
                ('sign', models.ImageField(blank=True, null=True, upload_to='category_sign/', verbose_name='Значек категории')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('mptt_level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='products.category', verbose_name='Родительская категория')),
            ],
            options={
                'verbose_name': 'Категория товаров',
                'verbose_name_plural': 'Категории товаров',
            },
        ),
        migrations.CreateModel(
            name='CategoryCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active_custom_order_group', models.BooleanField(default=True, verbose_name='Применить индивидуальный порядок групп атрибутов')),
                ('is_active_custom_order_shot_parameters', models.BooleanField(default=True, verbose_name='Применить индивидуальный порядок кратких характеристик')),
                ('is_active_custom_order_mini_parameters', models.BooleanField(default=True, verbose_name='Применить индивидуальный порядок мини характеристик')),
                ('category_list', mptt.fields.TreeManyToManyField(blank=True, default=None, to='products.Category', verbose_name='Список категорий')),
            ],
            options={
                'verbose_name': 'Набор категорий с индивидуальным порядком групп атрибутов',
                'verbose_name_plural': 'Наборы категорий с индивидуальным порядком групп атрибутов',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=64, null=True, unique=True)),
            ],
            options={
                'verbose_name': 'Страна',
                'verbose_name_plural': 'Страны',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default=None, max_length=128, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('slug', models.SlugField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('art', models.CharField(blank=True, default=None, max_length=10, null=True, unique=True, verbose_name='Артикул товара')),
                ('description', models.TextField(blank=True, default=None, null=True, verbose_name='Описание товара')),
                ('rating', models.SmallIntegerField(choices=[(1, ' * '), (2, ' * * '), (3, ' * * * '), (4, ' * * * * '), (5, ' * * * * * ')], db_index=True, default=1)),
                ('parameters', models.JSONField(blank=True, default=dict, verbose_name='Характеристики товара')),
                ('parameters_structure', models.JSONField(blank=True, default=dict, verbose_name='')),
                ('sorted_parameters_structure', models.JSONField(blank=True, default=list, verbose_name='Сортированная структура характеристик')),
                ('custom_order_group', models.JSONField(blank=True, default=list, verbose_name='Индивидуальный порядок групп атрибутов для сочетания категорий')),
                ('is_active_custom_order_group', models.BooleanField(default=True, verbose_name='Использоватть порядок групп атрибутов определенный в коллекции категорий')),
                ('shot_parameters_structure', models.JSONField(blank=True, default=dict, verbose_name='Структура кратких характеристик товара')),
                ('mini_parameters_structure', models.JSONField(blank=True, default=dict, verbose_name='Структура мини характеристик товара')),
                ('shot_parameters_custom_structure', models.JSONField(blank=True, default=dict, verbose_name='Структура кратких характеристик товара для сочетания категорий')),
                ('mini_parameters_custom_structure', models.JSONField(blank=True, default=dict, verbose_name='Структура мини характеристик товара для сочетания категорий')),
                ('length', models.FloatField(blank=True, null=True, verbose_name='Длина, см')),
                ('width', models.FloatField(blank=True, null=True, verbose_name='Ширина, см')),
                ('height', models.FloatField(blank=True, null=True, verbose_name='Высота, см')),
                ('length_box', models.FloatField(blank=True, null=True, verbose_name='Длина упаковки, см')),
                ('width_box', models.FloatField(blank=True, null=True, verbose_name='Ширина упаковки, см')),
                ('height_box', models.FloatField(blank=True, null=True, verbose_name='Высота упаковки, см')),
                ('weight', models.FloatField(blank=True, null=True, verbose_name='Вес, кг')),
                ('warranty', models.SmallIntegerField(choices=[(1, '12 мес.'), (2, '6 мес.'), (3, '3 мес.'), (4, '14 дней')], default=1, verbose_name='Срок гарантии')),
                ('url', models.URLField(blank=True, default=None, max_length=128, null=True, unique=True, verbose_name='Ссылка на товар на сайте производителя)')),
                ('admin_category', mptt.fields.TreeForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.category', verbose_name='Категория товаров админ-панели')),
                ('brand', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.brand', verbose_name='Торговая марка')),
                ('category_collection', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.categorycollection', verbose_name='Коллекция категорий')),
                ('made_in', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.country', verbose_name='Страна производства')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Список товаров',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SomeSites',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=128, unique=True, verbose_name='Название магазина')),
                ('role', models.SmallIntegerField(choices=[(1, ' Покупатель '), (2, ' Поставщик '), (3, ' Конкурент ')])),
                ('info', models.CharField(blank=True, default=None, max_length=128, verbose_name='Краткое описание')),
                ('url', models.URLField(blank=True, default=None, max_length=128, null=True, unique=True, verbose_name='Ссылка на сайт)')),
            ],
            options={
                'verbose_name': 'Сторонний сайт',
                'verbose_name_plural': 'Сторонние сайты',
            },
        ),
        migrations.CreateModel(
            name='ShotParametersOfProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, default='', max_length=128, null=True, unique=True, verbose_name='Название для кратких характеристик (оставить пустым если названиие атрибута желаете оставить тем же)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Отображать в кратких характеристиках товара')),
                ('position', models.PositiveIntegerField(null=True, verbose_name='Position')),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.attributesingroup', verbose_name='Атрибут для отображения в кратких характеристиках')),
                ('category', mptt.fields.TreeForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_shot_attributes', to='products.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Атрибут для отображения в блоке кратких характеристик товаров',
                'verbose_name_plural': 'Блок кратких характеристик товаров',
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='ProductInCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_category', models.PositiveIntegerField(default=0, verbose_name='PositionCategory')),
                ('position_product', models.PositiveIntegerField(blank=True, null=True, verbose_name='PositionProduct')),
                ('category', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_products', to='products.category', verbose_name='Категория')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_categories', to='products.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Размещение товара в категории ',
                'verbose_name_plural': 'Размещения товара в категории',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, default='', max_length=128, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('image', models.ImageField(blank=True, null=True, upload_to='product_images/', verbose_name='Фото товара')),
                ('is_main_1', models.BooleanField(default=True, verbose_name='Главное фото')),
                ('is_main_2', models.BooleanField(default=True, verbose_name='Главное фото при наведении')),
                ('position', models.PositiveIntegerField(null=True, verbose_name='Position')),
                ('product', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_image', to='products.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Фотография товара',
                'verbose_name_plural': 'Фотографии товаров',
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='PricesOtherShop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Изменено')),
                ('url', models.URLField(blank=True, default=None, max_length=128, null=True, unique=True, verbose_name='Ссылка на товар)')),
                ('info', models.CharField(blank=True, default=None, max_length=128, null=True, verbose_name='Краткое описание)')),
                ('product', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.product', verbose_name='Товар')),
                ('shop', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.somesites', verbose_name='Магазин')),
            ],
            options={
                'verbose_name': 'Цена конкурента',
                'verbose_name_plural': 'Цены конкурентов',
            },
        ),
        migrations.CreateModel(
            name='MiniParametersOfProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, default='', max_length=128, null=True, unique=True, verbose_name='Название для атрибута в выдаче товаров (оставить пустым если названиие атрибута желаете оставить тем же)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Отображать в мини характеристиках товара')),
                ('position', models.PositiveIntegerField(null=True, verbose_name='Position')),
                ('attribute', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.attributesingroup', verbose_name='Атрибут для отображения в мини характеристиках')),
                ('category', mptt.fields.TreeForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_mini_attributes', to='products.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Атрибут для отображения в выдаче товаров',
                'verbose_name_plural': 'Блок хар-к для выдачи товаров',
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='ItemOfCustomOrderGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('position', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Position')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.category', verbose_name='Категория')),
                ('category_collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rel_group_iocog', to='products.categorycollection', verbose_name='Набор категорий')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rel_cat_collection_iocog', to='products.attrgroup', verbose_name='Группа атрибутов')),
            ],
            options={
                'verbose_name': 'Группа атрибутов набора категорий товаров',
                'verbose_name_plural': 'Группы атрибутов набора категорий товаров',
            },
        ),
        migrations.AddField(
            model_name='brand',
            name='country',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.country', verbose_name='Страна брэнда'),
        ),
        migrations.AddField(
            model_name='attribute',
            name='value_list',
            field=models.ManyToManyField(blank=True, default=None, to='products.AttributeValue', verbose_name='Список значений'),
        ),
        migrations.CreateModel(
            name='AttrGroupInCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Position')),
                ('category', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_groups', to='products.category', verbose_name='Категория товаров')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_categories', to='products.attrgroup', verbose_name='Группа атрибутов')),
            ],
            options={
                'verbose_name': 'Группа атрибутов категории',
                'verbose_name_plural': 'Группы атрибутов категории',
                'ordering': ['position'],
                'unique_together': {('category', 'group')},
            },
        ),
    ]
