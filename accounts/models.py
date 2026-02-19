from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model with company and role support
    """

    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('company_admin', 'Company Admin'),
        ('engineer', 'Engineer'),
    ]

    # 🔴 IMPORTANT FIX 1:
    # Company ko STRING reference se import karo (circular import avoid)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,   # 🔴 IMPORTANT FIX 2
        related_name="users",
        null=True,
        blank=True,
        help_text="Company this user belongs to (null for super admin)"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='engineer'
    )

    avatar = models.ImageField(
        upload_to='user_avatars/',
        blank=True,
        null=True
    )

    phone = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # --------------------
    # ROLE HELPERS
    # --------------------
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_company_admin(self):
        return self.role == 'company_admin'

    @property
    def is_engineer(self):
        return self.role == 'engineer'

    # --------------------
    # PERMISSIONS
    # --------------------
    def can_manage_users(self):
        return self.is_super_admin or self.is_company_admin

    def can_delete_incidents(self):
        return self.is_super_admin or self.is_company_admin
