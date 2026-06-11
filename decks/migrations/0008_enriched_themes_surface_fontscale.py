from django.db import migrations, models


def convert_font_size(apps, schema_editor):
    """Map old integer font_size to s/m/l. <=32→s, >=44→l, else→m."""
    Deck = apps.get_model('decks', 'Deck')
    for deck in Deck.objects.all():
        old = deck.font_size_int
        if old <= 32:
            deck.font_size_new = 's'
        elif old >= 44:
            deck.font_size_new = 'l'
        else:
            deck.font_size_new = 'm'
        deck.save(update_fields=['font_size_new'])


def reverse_convert_font_size(apps, schema_editor):
    Deck = apps.get_model('decks', 'Deck')
    mapping = {'s': 36, 'm': 40, 'l': 46}
    for deck in Deck.objects.all():
        deck.font_size_int = mapping.get(deck.font_size_new, 40)
        deck.save(update_fields=['font_size_int'])


class Migration(migrations.Migration):

    dependencies = [
        ('decks', '0007_add_resource_to_oauth'),
    ]

    operations = [
        # ── Theme enrichment ──────────────────────────────────────────────────
        migrations.AddField(
            model_name='theme',
            name='font_heading',
            field=models.CharField(default='Inter', max_length=120),
        ),
        migrations.AddField(
            model_name='theme',
            name='font_body',
            field=models.CharField(default='Inter', max_length=120),
        ),
        migrations.AddField(
            model_name='theme',
            name='font_mono',
            field=models.CharField(default='JetBrains Mono', max_length=120),
        ),
        migrations.AddField(
            model_name='theme',
            name='heading_color',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='accent_2',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='rule_color',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='bg_gradient',
            field=models.TextField(blank=True, null=True),
        ),

        # ── Deck: add surface ─────────────────────────────────────────────────
        migrations.AddField(
            model_name='deck',
            name='surface',
            field=models.CharField(
                choices=[('blank', 'Blank'), ('dots', 'Dots'), ('rules', 'Rules')],
                default='blank',
                max_length=8,
            ),
        ),

        # ── Deck: migrate font_size int → char ────────────────────────────────
        # Step 1: rename old int field to a temp name via db_column trick
        migrations.RenameField(
            model_name='deck',
            old_name='font_size',
            new_name='font_size_int',
        ),
        # Step 2: add new char field (temp Python name)
        migrations.AddField(
            model_name='deck',
            name='font_size_new',
            field=models.CharField(
                choices=[('s', 'Small'), ('m', 'Medium'), ('l', 'Large')],
                default='m',
                max_length=1,
            ),
        ),
        # Step 3: data migration
        migrations.RunPython(convert_font_size, reverse_convert_font_size),
        # Step 4: drop the old int column
        migrations.RemoveField(model_name='deck', name='font_size_int'),
        # Step 5: rename new char field to font_size
        migrations.RenameField(
            model_name='deck',
            old_name='font_size_new',
            new_name='font_size',
        ),
    ]
