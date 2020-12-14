# Generated by Django 3.1.4 on 2020-12-14 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Emails_Historico',
            fields=[
                ('indice', models.AutoField(primary_key=True, serialize=False, unique=True)),
                ('usuario', models.CharField(max_length=255)),
                ('texto', models.TextField(blank=True)),
                ('result', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Quota_Info',
            fields=[
                ('usuario', models.CharField(max_length=255, primary_key=True, serialize=False, unique=True)),
                ('quota', models.IntegerField(default=10)),
                ('quota_used', models.IntegerField(default=0)),
            ],
        ),
    ]
