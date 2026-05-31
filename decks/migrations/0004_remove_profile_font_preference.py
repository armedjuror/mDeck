from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('decks', '0003_deck_font'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='font_preference',
        ),
    ]
