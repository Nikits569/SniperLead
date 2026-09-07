from .models import CategoriesType
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout  # Импортируем логаут
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from .forms import LoginForm, RegisterForm
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.utils.translation import gettext_lazy as _

def generate_telegram_link(request):
  token = uuid.uuid4().hex
  request.user.tg_token = token
  request.user.save()

  bot_username = "YourSniperLeadBot"  # Имя твоего бота в Telegram
  link = f"https://t.me/{bot_username}?start=link_{token}"
  return JsonResponse({'link': link})

def login(request):
  if request.user.is_authenticated:
    return redirect('/')

  form = LoginForm(request.POST or None)

  if request.method == 'POST' and form.is_valid():
    email = form.cleaned_data.get('email')
    password = form.cleaned_data.get('password')
    user = authenticate(request, email=email, password=password)

    if user is not None:
        auth_login(request, user)
        return redirect('profile')
    else:
        form.add_error(None, _('Неверный email или пароль'))

  return render(request, 'account/login.html', {'form': form})


def logout(request):
  # Очищаем сессию пользователя и перенаправляем на главную
  auth_logout(request)
  return redirect('/')


def signup(request):
  if request.user.is_authenticated:
    return redirect('/')

  form = RegisterForm(request.POST or None)

  if request.method == 'POST' and form.is_valid():
    user = form.save()
    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('profile')
  else:
    print(form.errors)

  return render(request, 'account/signup.html', {'form': form})


@csrf_exempt
def profile(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      print('ДАННЫЕ ОТ ФРОНТА:', data)

      selected_cats = data.get('categories', [])
      email_notif = data.get('email_notification')

      # Исправленные ключи планов (раздельно trial и pro)
      plan_limits = {'starter': 1, 'trial/pro': 3, 'pro': 3, 'business': 999}
      user_plan = request.user.plan
      max_allowed = plan_limits.get(user_plan, 0)

      # Проверяем лимит категорий ДО сохранения
      if len(selected_cats) > max_allowed:
        return JsonResponse(
            {'status': 'error', 'message': 'Limit exceeded'}, status=400
        )

      # Обновляем данные пользователя
      request.user.categories = selected_cats
      if email_notif is not None:
        request.user.email_notification = email_notif

      request.user.save()
      print('БАЗА ОБНОВЛЕНА. Email status:', request.user.email_notification)

      return JsonResponse({'status': 'success'})

    except Exception as e:
      print('ОШИБКА СОХРАНЕНИЯ:', e)
      return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

  # GET запрос
  plan_limits = {'starter': 1, 'trial/pro': 3, 'pro': 3, 'business': 999}

  user_plan = request.user.plan
  context = {
    'categories_choices': CategoriesType.choices,
    'max_categories': plan_limits.get(user_plan, 0),  # дефолт 0, не 1
  }

  return render(request, 'account/profile.html', context)