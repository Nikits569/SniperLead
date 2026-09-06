from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Profile

User = get_user_model()


class RegisterForm(forms.ModelForm):

    name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={'placeholder': _('Name')}),
    )

    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'placeholder': _('Email')}),
    )

    password = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={
            'placeholder': _('пароль'),
        })
    )

    class Meta:
        model = User
        fields = ('name', 'email', 'password')
        widgets = {

            'name': forms.TextInput(attrs={
                'placeholder': _("Name"),
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': _('email'),
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': _('password'),
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('користувач із таким email вже існує')
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'placeholder': _('email'),
        })
    )
    password = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={
            'placeholder': _('пароль'),
        })
    )

class ProfileCategoriesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['categories']

    def clean_categories(self):
        categories = self.cleaned_data.get('categories', [])
        user = self.instance

        # Лимиты в зависимости от тарифа
        limits = {
            'starter': 1,
            'trial/pro': 3,
            'pro': 3,
            'business': 999  # Без лимита
        }

        max_allowed = limits.get(user.plan, 1)

        if len(categories) > max_allowed:
            raise forms.ValidationError(
                f"Ваш тарифный план ({user.plan}) позволяет выбрать максимум {max_allowed} категорий."
            )
        return categories