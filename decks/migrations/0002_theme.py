import django.db.models.deletion
from django.db import migrations, models


THEME_DATA = [
    {'slug': 'dark',   'name': 'Dark',   'bg': '#0f0f0f', 'text': '#e0e0e0', 'accent': '#4ade80', 'code_bg': '#1a1a1a'},
    {'slug': 'chalk',  'name': 'Chalk',  'bg': '#1a1a2e', 'text': '#eaeaea', 'accent': '#a78bfa', 'code_bg': '#16213e'},
    {'slug': 'sepia',  'name': 'Sepia',  'bg': '#1c1814', 'text': '#d4c5a9', 'accent': '#f59e0b', 'code_bg': '#231f1a'},
    {'slug': 'ocean',  'name': 'Ocean',  'bg': '#0a1628', 'text': '#e2e8f0', 'accent': '#38bdf8', 'code_bg': '#0f2040'},
    {'slug': 'paper',  'name': 'Paper',  'bg': '#f5f0e8', 'text': '#1a1a1a', 'accent': '#dc2626', 'code_bg': '#e8e0d0'},
    {'slug': 'forest', 'name': 'Forest', 'bg': '#0d1f0d', 'text': '#d4edda', 'accent': '#4ade80', 'code_bg': '#122012'},
]


def create_themes(apps, schema_editor):
    Theme = apps.get_model('decks', 'Theme')
    for td in THEME_DATA:
        Theme.objects.get_or_create(slug=td['slug'], defaults=td)


def link_decks_to_themes(apps, schema_editor):
    Theme = apps.get_model('decks', 'Theme')
    Deck = apps.get_model('decks', 'Deck')
    theme_map = {t.slug: t for t in Theme.objects.all()}
    dark = theme_map.get('dark')
    for deck in Deck.objects.all():
        deck.theme = theme_map.get(deck.theme_slug, dark)
        deck.save(update_fields=['theme'])


def reverse_link(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('decks', '0001_initial'),
    ]

    operations = [
        # 1. Create Theme table
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=50)),
                ('bg', models.CharField(max_length=20)),
                ('text', models.CharField(max_length=20)),
                ('accent', models.CharField(max_length=20)),
                ('code_bg', models.CharField(max_length=20)),
            ],
            options={'ordering': ['name']},
        ),

        # 2. Populate themes
        migrations.RunPython(create_themes, migrations.RunPython.noop),

        # 3. Rename old theme varchar column so we can add new FK field named 'theme'
        migrations.RenameField(
            model_name='deck',
            old_name='theme',
            new_name='theme_slug',
        ),

        # 4. Add new FK field (creates theme_id column)
        migrations.AddField(
            model_name='deck',
            name='theme',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='decks',
                to='decks.theme',
            ),
        ),

        # 5. Copy data: set theme FK based on old theme_slug value
        migrations.RunPython(link_decks_to_themes, reverse_link),

        # 6. Drop the old varchar column
        migrations.RemoveField(
            model_name='deck',
            name='theme_slug',
        ),
    ]
