from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_alter_orderitem_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_code',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='product',
            name='load_limit',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='product',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='price_retail',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='price_special',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='product',
            name='wire_section',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]

