from django.db import models

class AdminUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.TextField()
    email = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'admin_users'


class Requests(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.CharField(max_length=150, unique=True)
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
    image_url = models.CharField(max_length=500, blank=True, null=True)  # može URL
    image = models.ImageField(upload_to='offer_images/', blank=True, null=True)  # može fajl
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
        related_name='responses_sent'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.admin} to {self.request}"

    class Meta:
        db_table = 'response'