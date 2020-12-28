from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from datetime import datetime


def get_filename(self, filename):
    """ Generates a custom filename for uploads based on author's username and the post's creation date """

    extension = filename.split('.')[-1]
    t = datetime.now()
    datetime_str = f"{t.year}-{t.month}-{t.day}-{t.hour}{t.minute}{t.second}"

    return f"uploads/profiles/{self.user.username}_{datetime_str}.{extension}"


class UserManager(BaseUserManager):

    def create_user(self, email, password, first_name, last_name, username):
        """ Creates and saves a user """

        self.validate_required_fields(email, first_name, last_name, username)

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username.lower()
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, first_name, last_name, username):
        """ Creates and saves a superuser """

        user = self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        user.is_admin = True
        user.is_staff = True

        user.save(using=self._db)
        return user

    def validate_required_fields(self, email, first_name, last_name, username):
        """ Raises value errors if any required field is None """

        if not email:
            raise ValueError('Please provide a valid email')
        elif not username:
            raise ValueError('Please provide a valid username')
        elif not first_name:
            raise ValueError('Please provide a first name')
        elif not last_name:
            raise ValueError('Please provide a last name')

        if slugify(username) != username.lower():
            raise ValidationError('Invalid username')

        return


class User(AbstractBaseUser):
    """ Custom user model users email as the identifier"""

    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.SlugField(max_length=50, unique=True)

    account_created = models.DateTimeField(auto_now_add=True)

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    def __str__(self):
        return self.email

    # has_perm and has_module_perms required to view users in Admin

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    blog_title = models.CharField(blank=True, null=True, max_length=255, help_text='Add a blog title or headline to go beneath your name')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(blank=True, null=True, upload_to=get_filename)
    cover_photo = models.ImageField(blank=True, null=True, upload_to=get_filename)
    city = models.CharField(blank=True, null=True, max_length=100)
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    website = models.URLField(help_text='You can add a link to your personal website', blank=True, null=True)
    twitter = models.CharField(max_length=16, blank=True, null=True)
    github = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username}) | {self.user.email}"

    def get_location(self):
        """ Returns a string with the user's location based on their chosen city/country. """
        if not self.city and not self.country:
            return

        if self.city:
            if self.country.name:
                return f"{self.city}, {self.country.name}"
            else:
                return f"{self.city}"
        else:
            return f"{self.country.name}"
