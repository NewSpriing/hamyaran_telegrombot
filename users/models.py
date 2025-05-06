from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django_jalali.db.models import jDateTimeField

class CustomUser(AbstractUser):
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن')], null=True, blank=True)
    medical_conditions = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)

    # Override groups and user_permissions to avoid reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.full_name

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=100)
    full_address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = jDateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.full_name}"

class FamilyMember(models.Model):
    RELATIONSHIP_CHOICES = [
        ('father', 'پدر'),
        ('mother', 'مادر'),
        ('son', 'پسر'),
        ('daughter', 'دختر'),
        ('spouse', 'همسر'),
        ('sibling', 'خواهر/برادر'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='family_members')
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن')], null=True, blank=True)
    medical_conditions = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    created_at = jDateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.get_relationship_display()}) - {self.user.full_name}"

    class Meta:
        verbose_name = 'عضو خانواده'
        verbose_name_plural = 'اعضای خانواده'