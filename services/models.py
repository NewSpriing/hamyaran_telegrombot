from django.db import models

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'دسته‌بندی خدمت'
        verbose_name_plural = 'دسته‌بندی‌های خدمت'

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    duration = models.DurationField()

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمت‌ها'
        