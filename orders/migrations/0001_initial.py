# Generated by Django 3.2.6 on 2021-08-24 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('spaces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=45)),
                ('phone_number', models.CharField(max_length=200)),
                ('email', models.CharField(max_length=200)),
                ('purpose', models.CharField(max_length=200, null=True)),
                ('content', models.TextField(null=True)),
            ],
            options={
                'db_table': 'bookers',
            },
        ),
        migrations.CreateModel(
            name='OrderStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'statuses',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField()),
                ('date', models.DateField()),
                ('booker', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.booker')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spaces.option')),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spaces.space')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.orderstatus')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'orders',
            },
        ),
    ]
