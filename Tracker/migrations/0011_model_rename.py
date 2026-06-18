from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Tracker", "0010_budget_remove_defaults"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="GeneralSpendingLimit",
            new_name="GeneralBudget",
        ),
        migrations.RenameModel(
            old_name="CategorySpendingLimit",
            new_name="CategoryBudget",
        ),
    ]
