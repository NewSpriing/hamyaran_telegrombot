from django.db import models
import logging

logger = logging.getLogger(__name__)

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="دسته بندی والد")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'دسته‌بندی خدمت'
        verbose_name_plural = 'دسته‌بندی‌های خدمت'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f"ServiceCategory '{self.name}' (ID: {self.id}) created/updated.")

    def delete(self, *args, **kwargs):
        logger.warning(f"ServiceCategory '{self.name}' (ID: {self.id}) deleted.")
        super().delete(*args, **kwargs)

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name="دسته بندی")
    name = models.CharField(max_length=100, verbose_name="نام")
    description = models.TextField(verbose_name="توضیحات")
    price = models.PositiveIntegerField(verbose_name="قیمت")
    duration = models.DurationField(verbose_name="مدت زمان")

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمت‌ها'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f"Service '{self.name}' (ID: {self.id}) created/updated.")

    def delete(self, *args, **kwargs):
        logger.warning(f"Service '{self.name}' (ID: {self.id}) deleted.")
        super().delete(*args, **kwargs)