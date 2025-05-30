# Generated by Django 2.2.7 on 2021-12-17 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0026_auto_20211217_1002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='europecountry',
            name='national_supervisor_report_expires_in',
            field=models.IntegerField(default=14, help_text='Number of days that a report in the queue is exclusively available to the nagional supervisor. For example, if the field value is 6, after report_creation_time + 6 days a report will be available to all users'),
        ),
    ]
