# Generated migration for real-time odds update system

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0010_classement'),
    ]

    operations = [
        migrations.AddField(
            model_name='cote',
            name='paris_count_since_last_update',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='cote',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
