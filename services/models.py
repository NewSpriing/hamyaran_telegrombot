from django.db import models
from django_jalali.db import models as jmodels

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'دسته‌بندی خدمات'
        verbose_name_plural = 'دسته‌بندی‌های خدمات'

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)  # e.g., "01:30:00" for 1.5 hours
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمات'