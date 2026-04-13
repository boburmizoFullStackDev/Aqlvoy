from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{8,14}$',
    message='Enter a valid phone number (e.g. +998901234567).',
)


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required.')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        PARENT = 'parent', 'Parent'
        ADMIN = 'admin', 'Admin'

    phone = models.CharField(
        max_length=20, unique=True, validators=[phone_validator],
        verbose_name='Phone number',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    grade = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        help_text='School grade 1–11. Applicable to students only.',
    )
    class Gender(models.TextChoices):
        MALE   = 'male',   'Male'
        FEMALE = 'female', 'Female'

    class VoiceTone(models.TextChoices):
        NEUTRAL   = 'neutral',   'Neutral'
        WARM      = 'warm',      'Warm'
        ENERGETIC = 'energetic', 'Energetic'

    total_points     = models.PositiveIntegerField(default=0)
    avatar           = models.ImageField(upload_to='avatars/', blank=True, null=True)
    character_gender = models.CharField(
        max_length=10, choices=Gender.choices, default=Gender.MALE,
    )
    voice_tone = models.CharField(
        max_length=15, choices=VoiceTone.choices, default=VoiceTone.NEUTRAL,
    )

    # Parent → child self-referential M2M (asymmetric)
    children = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parents',
        help_text='Parents can link to their student children.',
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.first_name} ({self.phone})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()


# Forward-reference fix for create_superuser default
User.Role = User.Role
