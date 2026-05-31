from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decks', '0002_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='deck',
            name='font',
            field=models.CharField(
                max_length=100,
                default='JetBrains Mono',
                choices=[
                    ('JetBrains Mono', 'JetBrains Mono'),
                    ('Inter', 'Inter'),
                    ('Merriweather', 'Merriweather'),
                    ('Lora', 'Lora'),
                    ('DM Sans', 'DM Sans'),
                    ('Fraunces', 'Fraunces'),
                    ('Outfit', 'Outfit'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='deck',
            name='font_size',
            field=models.PositiveSmallIntegerField(default=40),
        ),
    ]
