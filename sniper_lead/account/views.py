from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout  # Импортируем логаут
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from .forms import LoginForm, RegisterForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Profile, CategoriesType

@login_required
def generate_telegram_link(request):
    token = uuid.uuid4().hex
    request.user.tg_token = token
    request.user.tg_token_created_at = timezone.now()  # см. миграцию ниже
    request.user.save()

    bot_username = settings.TELEGRAM_BOT_USERNAME  # вынести в settings/.env
    link = f"https://t.me/{bot_username}?start=link_{token}"
    return JsonResponse({'link': link})


# --- 2. НОВОЕ: бот дергает это, когда юзер нажал /start link_<token> ---
@csrf_exempt
@require_POST
def telegram_link_confirm(request):
    # Это внутренний эндпоинт бот → сайт, не для браузера.
    # Защищаем общим секретом, а не CSRF/сессией.
    secret = request.headers.get('X-Bot-Secret')
    if secret != settings.BOT_INTERNAL_SECRET:
        return JsonResponse({'status': 'error', 'message': 'forbidden'}, status=403)

    try:
        data = json.loads(request.body)
        token = data.get('token')
        telegram_id = data.get('telegram_id')
        telegram_username = data.get('telegram_username', '')
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'bad_request'}, status=400)

    if not token or not telegram_id:
        return JsonResponse({'status': 'error', 'message': 'missing_fields'}, status=400)

    try:
        user = Profile.objects.get(tg_token=token)
    except Profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'invalid_token'}, status=404)

    # TTL токена — 10 минут, чтобы старая ссылка не работала вечно
    if user.tg_token_created_at and (timezone.now() - user.tg_token_created_at).total_seconds() > 600:
        return JsonResponse({'status': 'error', 'message': 'token_expired'}, status=400)

    # Один Telegram-аккаунт — один профиль сайта
    if Profile.objects.filter(telegram_id=telegram_id).exclude(id=user.id).exists():
        return JsonResponse({'status': 'error', 'message': 'telegram_already_linked'}, status=409)

    user.telegram_id = telegram_id
    user.telegram = telegram_username
    user.telegram_notification = True
    user.tg_token = None  # токен одноразовый — сжигаем сразу
    user.tg_token_created_at = None
    user.save()

    # Возвращаем боту всё, что нужно для приветственного сообщения
    return JsonResponse({
        'status': 'success',
        'plan': user.plan,
        'categories': user.categories,
        'end_at': user.end_at.isoformat() if user.end_at else None,
    })


# --- 3. НОВОЕ: отвязка из личного кабинета ---
@login_required
@require_POST
def telegram_unlink(request):
    request.user.telegram_id = None
    request.user.telegram = None
    request.user.telegram_notification = False
    request.user.save()
    return JsonResponse({'status': 'success'})

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


