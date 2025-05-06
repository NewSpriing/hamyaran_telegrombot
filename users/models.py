from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('شماره تلفن باید وارد شود'))
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100, verbose_name='نام و نام خانوادگی')
    phone_number = models.CharField(max_length=20, unique=True, verbose_name='شماره تلفن')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن')], verbose_name='جنسیت')
    medical_conditions = models.TextField(blank=True, verbose_name='بیماری‌های زمینه‌ای')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    region = models.CharField(max_length=100, blank=True, verbose_name='منطقه')
    username = None  # Remove username field
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'gender']

    objects = CustomUserManager()

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        if not self.birth_date:
            return None
        from jdatetime import date
        today = date.today()
        birth_date = date.fromgregorian(date=self.birth_date)
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses', verbose_name='کاربر')
    title = models.CharField(max_length=50, verbose_name='عنوان آدرس')
    full_address = models.TextField(verbose_name='آدرس کامل')
    latitude = models.FloatField(null=True, blank=True, verbose_name='عرض جغرافیایی')
    longitude = models.FloatField(null=True, blank=True, verbose_name='طول جغرافیایی')

    def __str__(self):
        return f"{self.title} - {self.user.full_name}"

class FamilyMember(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='family_members', verbose_name='کاربر')
    full_name = models.CharField(max_length=100, verbose_name='نام و نام خانوادگی')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن')], verbose_name='جنسیت')
    medical_conditions = models.TextField(blank=True, verbose_name='بیماری‌های زمینه‌ای')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    region = models.CharField(max_length=100, blank=True, verbose_name='منطقه')
    relationship = models.CharField(max_length=50, verbose_name='نسبت')

    def __str__(self):
        return f"{self.full_name} ({self.relationship})"

    @property
    def age(self):
        if not self.birth_date:
            return None
        from jdatetime import date
        today = date.today()
        birth_date = date.fromgregorian(date=self.birth_date)
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age

class Document(models.Model):
    family_member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='documents', verbose_name='عضو خانواده')
    file = models.FileField(upload_to='documents/', verbose_name='فایل')
    description = models.CharField(max_length=200, verbose_name='توضیحات')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ آپلود')

    def __str__(self):
        return f"{self.description} - {self.family_member.full_name}"
    