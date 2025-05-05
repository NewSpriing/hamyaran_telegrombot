from django.db import models
from users.models import CustomUser, Address, FamilyMember
from services.models import Service
from django_jalali.db import models as jmodels

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    recipient = models.ForeignKey(FamilyMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    preferred_gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن'), ('any', 'فرقی ندارد')], default='any')
    special_conditions = models.TextField(null=True, blank=True)
    scheduled_time = jmodels.jDateTimeField()
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('confirmed', 'تأیید شده'),
        ('completed', 'تکمیل شده'),
        ('canceled', 'لغو شده'),
    ], default='pending')

    def __str__(self):
        recipient_name = self.recipient.full_name if self.recipient else self.user.full_name
        return f"Order {self.id} - {recipient_name} - {self.service.name}"

    class Meta:
        verbose_name = 'درخواست'
        verbose_name_plural = 'درخواست‌ها'
        