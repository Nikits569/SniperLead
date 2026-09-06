import uuid
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager


class PlanType(models.TextChoices):
    TRIL_PRO = 'trial/pro'
    STARTER = 'starter'
    PRO = 'pro'
    BUSINESS = 'business'

class CategoriesType(models.TextChoices):
    REAL_ESTATE_RENT = "real_estate_rent", _("🏠 Оренда житла")
    REAL_ESTATE_ROOMMATE = "real_estate_roommate", _("🛏 Пошук сусіда / кімнати")

    VNZ_AND_RESIDENCE = "vnz_and_residence", _("📑 ВНЖ, ПМЖ та Терміни")
    DOCUMENTS_AND_TRANSLATIONS = "documents_and_translations", _("✍️ Переклади та Довідки")
    LEGAL_AND_LAWYERS = "legal_and_lawyers", _("⚖️ Юристи та Право")
    ACCOUNTING_AND_TAXES = "accounting_and_taxes", _("📊 Бухгалтерія та Податки")

    CONSTRUCTION_AND_MASTERS = "construction_and_masters", _("🧱 Будівництво та Майстри")
    HOME_REPAIR_AND_CLEANING = "home_repair_and_cleaning", _("🛠 Ремонт дому та Клінінг")
    TECH_AND_GADGET_REPAIR = "tech_and_gadget_repair", _("💻 Ремонт техніки та ПК")

    LOGISTICS_AND_MOVING = "logistics_and_moving", _("🚚 Вантажні перевезення")
    ERRANDS_AND_DELIVERY = "errands_and_delivery", _("📦 Дрібні посилки та Ліки")
    AUTO_REPAIR_AND_CARE = "auto_repair_and_care", _("🚗 СТО та Детейлінг")

    CHILDCARE_AND_NANNY = "childcare_and_nanny", _("👶 Няні та Догляд за дітьми")
    MEDICAL_AND_HEALTH = "medical_and_health", _("🩺 Лікарі та Медицина")
    VETERINARY_AND_PETS = "veterinary_and_pets", _("🐾 Ветеринари та Тварини")
    EDUCATION_AND_TUTORS = "education_and_tutors", _("🎓 Репетитори та Мови")

    IT_AND_DIGITAL = "it_and_digital", _("🌐 IT, Боти та Сайти")

class ProfileManager(BaseUserManager):
    use_in_migrations = True  # Важно для миграций кастомной модели

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Здесь пароль хэшируется
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class Profile(AbstractUser):
    # Удаляем стандартный username, так как входим по email
    username = None

    # Делаем email уникальным (ОБЯЗАТЕЛЬНО для логина)
    email = models.EmailField(unique=True, verbose_name=_('Email address'))

    email_verification_token = models.CharField(
        max_length=36,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('Email verification token')
    )

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    categories = models.JSONField(default=list, blank=True)
    plan = models.CharField(choices=PlanType.choices, max_length=100, default=None, null=True, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    telegram = models.CharField(max_length=200, verbose_name=_('Telegram'), null=True, blank=True)
    telegram_id = models.BigIntegerField(blank=True, null=True, unique=True)
    tg_token = models.CharField(max_length=64, blank=True, null=True)

    telegram_notification = models.BooleanField(default=False)
    email_notification = models.BooleanField(default=True)
    whatsapp = models.CharField(max_length=200, verbose_name=_('Whatsapp'), null=True, blank=True)
    whatsapp_notification = models.BooleanField(default=False)

    has_used_trial = models.BooleanField(default=False)

    # 1. Привязываем твой менеджер
    objects = ProfileManager()

    # 2. Указываем, что входим по email
    USERNAME_FIELD = 'email'

    # 3. Поля, которые консоль запросит при createsuperuser (кроме email и пароля)
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')

    @property
    def days_remaining(self):
        if not self.end_at:
            return 0

        delta = self.end_at - timezone.now()
        return max(0, delta.days)

