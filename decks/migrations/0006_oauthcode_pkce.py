from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decks', '0005_oauthapp_oauthcode_oauthtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='oauthcode',
            name='code_challenge',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='oauthcode',
            name='code_challenge_method',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]
