from django.db import models
from accounts.models import User, UserProfile
from accounts.utils import send_notification
from datetime import time, date, datetime

class Vendor(models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_slug = models.SlugField(max_length=100, unique=True)
    vendor_license = models.ImageField(upload_to='vendor/license')
    is_approved = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendor_name

    def is_open(self):
        # Check current day's opening hours.
        today_date = date.today()
        # isoweekday return no. from day
        today = today_date.isoweekday()
        current_opening_hours = OpeningHour.objects.filter(vendor=self, day=today)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        is_open = None
        for i in current_opening_hours:
            if not i.is_closed:
                start = str(datetime.strptime(i.from_hour, "%H:%M").time())
                end = str(datetime.strptime(i.to_hour, "%H:%M").time())
                # make current_time equal start and end by str
                if current_time > start and current_time < end:
                    is_open = True
                    break
                else:
                    is_open = False
        return is_open
#check is_approeved
    def save(self, *args, **kwargs):
        # check is_approved
        if self.pk is not None:
            # Update
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = 'accounts/emails/admin_approved_email.html'
                context = {
                    'user': self.user,
                    'is_approved': self.is_approved,
                    'to_email': self.user.email,
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

DAYS = [
    (1, ("Maandag")),
    (2, ("Dinsdag")),
    (3, ("Woensdag")),
    (4, ("Donderdag")),
    (5, ("Frijdag")),
    (6, ("Zaterdag")),
    (7, ("Zondag")),
    ]
HOUR_OF_DAY_24 = [(time(h, m).strftime('%H:%M'), time(h, m).strftime('%H:%M')) for h in range(0, 24) for m in (0, 30)]
class OpeningHour(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    from_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    to_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ('day', '-from_hour')
        unique_together = ('vendor', 'day', 'from_hour', 'to_hour')

    def __str__(self):
        return self.get_day_display()
