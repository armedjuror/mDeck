import hashlib
import secrets
import string
import random

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


def generate_unique_slug(title, model_class=None):
    base = slugify(title)[:50] or 'deck'
    slug = base
    if model_class is None:
        from decks.models import Deck
        model_class = Deck
    while model_class.objects.filter(slug=slug).exists():
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        slug = base[:45] + '-' + suffix
    return slug


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} profile'


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'slug')
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name

    def deck_count(self):
        return self.deck_set.count()


class Theme(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)
    bg = models.CharField(max_length=20)
    text = models.CharField(max_length=20)
    accent = models.CharField(max_length=20)
    code_bg = models.CharField(max_length=20)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Deck(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('published', 'Published'),
    ]
    FONT_CHOICES = [
        ('JetBrains Mono', 'JetBrains Mono'),
        ('Inter', 'Inter'),
        ('Merriweather', 'Merriweather'),
        ('Lora', 'Lora'),
        ('DM Sans', 'DM Sans'),
        ('Fraunces', 'Fraunces'),
        ('Outfit', 'Outfit'),
    ]
    FONT_CSS_MAP = {
        'JetBrains Mono': "'JetBrains Mono', monospace",
        'Inter':          "'Inter', sans-serif",
        'Merriweather':   "'Merriweather', serif",
        'Lora':           "'Lora', serif",
        'DM Sans':        "'DM Sans', sans-serif",
        'Fraunces':       "'Fraunces', serif",
        'Outfit':         "'Outfit', sans-serif",
    }
    FONT_SIZE_CHOICES = [(s, f'{s}px') for s in (28, 32, 36, 40, 44, 48, 52)]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    content = models.TextField()
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='deck_set'
    )
    tags = models.CharField(max_length=500, blank=True)
    theme = models.ForeignKey(
        'Theme', null=True, blank=True, on_delete=models.SET_NULL, related_name='decks'
    )
    font = models.CharField(max_length=100, choices=FONT_CHOICES, default='JetBrains Mono')
    font_size = models.PositiveSmallIntegerField(default=40)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    allow_copy = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def font_css_value(self):
        return self.FONT_CSS_MAP.get(self.font, "'JetBrains Mono', monospace")

    def tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def slide_count(self):
        return len([s for s in self.content.split('\n---\n') if s.strip()])


def _trim_versions(deck):
    versions = deck.versions.order_by('-saved_at')
    count = versions.count()
    if count > 20:
        ids_to_delete = list(versions.values_list('id', flat=True)[20:])
        DeckVersion.objects.filter(id__in=ids_to_delete).delete()


class DeckVersion(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.deck.title} @ {self.saved_at:%Y-%m-%d %H:%M}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _trim_versions(self.deck)


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=128)
    prefix = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.name} ({self.prefix}****)'

    @classmethod
    def generate(cls, user, name):
        raw_key = 'mdeck_' + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:10]
        api_key = cls.objects.create(
            user=user,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
        )
        return api_key, raw_key

    @classmethod
    def validate(cls, raw_key):
        from django.utils import timezone
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            api_key = cls.objects.select_related('user').get(key_hash=key_hash)
            api_key.last_used = timezone.now()
            api_key.save(update_fields=['last_used'])
            return api_key.user
        except cls.DoesNotExist:
            return None


class OAuthApp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauth_apps')
    name = models.CharField(max_length=100)
    client_id = models.CharField(max_length=80, unique=True)
    client_secret_hash = models.CharField(max_length=128)
    client_secret_prefix = models.CharField(max_length=14)
    redirect_uris = models.TextField(blank=True, help_text='One URI per line. Leave blank to allow any.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.name}'

    @classmethod
    def generate(cls, user, name):
        client_id = 'mdeck_cid_' + secrets.token_urlsafe(20)
        raw_secret = 'mdeck_cs_' + secrets.token_urlsafe(32)
        app = cls.objects.create(
            user=user,
            name=name,
            client_id=client_id,
            client_secret_hash=hashlib.sha256(raw_secret.encode()).hexdigest(),
            client_secret_prefix=raw_secret[:14],
        )
        return app, raw_secret

    def verify_secret(self, raw_secret):
        return hashlib.sha256(raw_secret.encode()).hexdigest() == self.client_secret_hash

    def get_redirect_uris(self):
        return [u.strip() for u in self.redirect_uris.splitlines() if u.strip()]


class OAuthCode(models.Model):
    app = models.ForeignKey(OAuthApp, on_delete=models.CASCADE, related_name='codes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=128, unique=True)
    redirect_uri = models.TextField()
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    code_challenge = models.CharField(max_length=256, blank=True, default='')
    code_challenge_method = models.CharField(max_length=10, blank=True, default='')
    resource = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-expires_at']


class OAuthToken(models.Model):
    app = models.ForeignKey(OAuthApp, on_delete=models.CASCADE, related_name='tokens')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    resource = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
