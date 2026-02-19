from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    """Multi-tenant company model"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    subscription_tier = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
