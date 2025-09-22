from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class AdminUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.TextField()
    email = models.CharField(max_length=255, blank=True, null=True)
    is_admin = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def id(self):
        return self.pk

    @property
    def is_active(self):
        return True

    class Meta:
        db_table = 'admin_users'


class Requests(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    contact = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    residence = models.CharField(max_length=100)
    postal = models.CharField(max_length=20)
    alcohol = models.BooleanField(default=False)
    smoker = models.BooleanField(default=False)
    employed = models.BooleanField(default=False)
    criminal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f"{self.name} {self.surname}"

    def set_password(self, raw_password):
        """Hashira lozinku i sprema je u model"""
        self.password = make_password(raw_password)
        self.save(update_fields=['password'])

    def check_password(self, raw_password):
        """Provjerava unesenu lozinku s hashiranim passwordom"""
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = 'requests'

class RelocationRequest(models.Model):
        request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name="relocations")

        city = models.CharField(max_length=100)
        postcode = models.CharField(max_length=20)
        stay_type = models.CharField(max_length=20)  # Temporary / Permanent
        accommodation_type = models.CharField(max_length=20)  # Apartment / House
        for_whom = models.CharField(max_length=50)
        others = models.CharField(max_length=255, blank=True, default='')

        pet = models.BooleanField(default=False)
        pet_type = models.CharField(max_length=100, blank=True, default='')

        distance = models.IntegerField(null=True, blank=True)
        price_range = models.CharField(max_length=50, blank=True, default='')

        req_parking = models.BooleanField(default=False)
        req_garage = models.BooleanField(default=False)
        req_balcony = models.BooleanField(default=False)
        req_terrace = models.BooleanField(default=False)
        req_shops = models.BooleanField(default=False)
        req_center = models.BooleanField(default=False)
        req_hospital = models.BooleanField(default=False)

        message = models.TextField(blank=True, default='')
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            db_table = 'relocation_requests'


class TimeRequest(models.Model):
    request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='time_requests')
    accommodation_date = models.DateField()
    know_duration = models.BooleanField()
    duration = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'time_requests'


class RefreshToken(models.Model):
    user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'refresh_tokens'


class Offer(models.Model):
    request = models.ForeignKey(Requests, on_delete=models.CASCADE, related_name='offers')
    type = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offers'


class OfferImage(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='offer_images/')
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offer_images'


class Response(models.Model):
    request = models.ForeignKey(
        'Requests',
        on_delete=models.CASCADE,
        related_name='responses'
    )
    admin = models.ForeignKey(
        'AdminUser',
        on_delete=models.CASCADE,
        related_name='responses_sent',
        null = True,
        blank = True
    )
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.admin:
            return f"Response by {self.admin} to {self.request}"
        return f"Response by User to {self.request}"

    class Meta:
        db_table = 'response'


class RequestUser(models.Model):
    request = models.OneToOneField('Requests', on_delete=models.CASCADE, related_name='user_profile')
    email = models.CharField(max_length=150)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.name} {self.surname}"

    @property
    def is_authenticated(self):
        return True  # ovo je ključno za DRF IsAuthenticated permission

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save(update_fields=['password'])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        db_table = 'requests_app_requestuser'


