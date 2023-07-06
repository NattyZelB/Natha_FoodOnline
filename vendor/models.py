from django.db import models
from accounts.models import User, UserProfile
from accounts.utils import send_notification
class Vendor(models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_license = models.ImageField(upload_to='vendor/license')
    is_approved = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendor_name

#check is_approeved
    def save(self, *args, **kwargs):
        # check is_approved
        if self.pk is not None:
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = 'accounts/emails/admin_approved_email.html'
                context = {
                    'user': self.user,
                    'is_approved': self.is_approved,
                }
            if self.is_approved == True:
                # Send notification email
                mail_subject = 'Gefeliciteerd! Uw restaurant is goedgekeurd.'
                send_notification(mail_subject, mail_template, context)
            else:
                # Send notification email
                mail_subject = 'Het spijt ons! U komt niet in aanmerking voor het publiceren van uw voedselmenu op onze marketplace.'
                send_notification(mail_subject, mail_template, context)
        return super(Vendor, self).save(*args, **kwargs)
