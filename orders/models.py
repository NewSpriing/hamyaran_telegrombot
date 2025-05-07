from django.db import models
from users.models import CustomUser, Address, FamilyMember
from services.models import Service
import logging

logger = logging.getLogger(__name__)

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', verbose_name="کاربر")
    recipient = models.ForeignKey(FamilyMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="گیرنده خدمت")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="خدمت")
    address = models.ForeignKey(Address, on_delete=models.CASCADE, verbose_name="آدرس")
    preferred_gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن'), ('any', 'فرقی ندارد')], default='any', verbose_name="جنسیت ترجیحی")
    special_conditions = models.TextField(null=True, blank=True, verbose_name="شرایط ویژه")
    scheduled_time = models.DateTimeField(verbose_name="زمان برنامه ریزی شده")  # Use DateTimeField
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")  # Use DateTimeField
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('confirmed', 'تأیید شده'),
        ('completed', 'تکمیل شده'),
        ('canceled', 'لغو شده'),
    ], default='pending', verbose_name="وضعیت")

    def __str__(self):
        recipient_name = self.recipient.full_name if self.recipient else self.user.full_name
        return f"سفارش {self.id} - {recipient_name} - {self.service.name}"

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        logger.info(f"Order {self.id} created/updated.")

    def delete(self, *args, **kwargs):
        logger.warning(f"Order {self.id} deleted.")
        super().delete(*args, **kwargs)