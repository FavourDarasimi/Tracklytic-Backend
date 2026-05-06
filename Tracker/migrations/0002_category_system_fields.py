from django.db import migrations, models


def create_system_categories(apps, schema_editor):
    Category = apps.get_model('Tracker', 'Category')
    system_categories = [
        {'name': 'Food', 'type': 'Expense', 'icon': 'FaUtensils', 'color': '#F59E0B'},
        {'name': 'Transport', 'type': 'Expense', 'icon': 'FaBus', 'color': '#3B82F6'},
        {'name': 'Bills', 'type': 'Expense', 'icon': 'FaFileInvoiceDollar', 'color': '#EF4444'},
        {'name': 'Entertainment', 'type': 'Expense', 'icon': 'FaFilm', 'color': '#A855F7'},
        {'name': 'Health', 'type': 'Expense', 'icon': 'FaHeartbeat', 'color': '#16A34A'},
        {'name': 'Shopping', 'type': 'Expense', 'icon': 'FaShoppingBag', 'color': '#10B981'},
        {'name': 'Salary', 'type': 'Income', 'icon': 'FaMoneyBillWave', 'color': '#14B8A6'},
        {'name': 'Business', 'type': 'Income', 'icon': 'FaBriefcase', 'color': '#0EA5E9'},
    ]

    for item in system_categories:
        category, created = Category.objects.get_or_create(
            name=item['name'],
            user=None,
            is_system=True,
            defaults={
                'type': item['type'],
                'tag': item['name'].lower(),
                'icon': item['icon'],
                'color': item['color'],
            },
        )
        if not created:
            category.type = item['type']
            category.tag = item['name'].lower()
            category.icon = item['icon']
            category.color = item['color']
            category.is_system = True
            category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('Tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_system',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.RunPython(create_system_categories),
    ]
