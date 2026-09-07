from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
import stripe
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from account.models import Profile
from .models import UserSubscription

stripe.api_key = settings.STRIPE_SECRET_KEY

# Уровни тарифов — чем выше число, тем "старше" тариф.
# Используется, чтобы решить, разрешать ли новую покупку
# (апгрейд — разрешаем, повтор того же или даунгрейд — блокируем).
PLAN_LEVELS = {
    None: 0,
    'starter': 1,
    'trial/pro': 2,
    'pro': 2,
    'business': 3,
}

PLAN_PRICES = {
    'starter': 'price_1UCikP4GOC7xoKdSFX6Nwuhc',
    'pro': 'price_1UCDEH4GOC7xoKdSCWnxT3MC',
    'business': 'price_1UCikd4GOC7xoKdSVA8zw7cM',
}


@method_decorator(login_required, name='dispatch')
class CreateCheckoutSessionView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body or '{}')
            requested_plan = data.get('plan', 'pro')

            if requested_plan not in PLAN_PRICES:
                return JsonResponse({'error': 'Neznámy tarif'}, status=400)

            # Проверяем, есть ли уже активная подписка
            try:
                sub = UserSubscription.objects.get(user=request.user)
                has_active_sub = sub.is_active
            except UserSubscription.DoesNotExist:
                has_active_sub = False

            if has_active_sub:
                current_level = PLAN_LEVELS.get(request.user.plan, 0)
                requested_level = PLAN_LEVELS.get(requested_plan, 0)

                if requested_level <= current_level:
                    return JsonResponse({
                        'error': 'Už máte tento alebo vyšší tarif. Ak chcete znížiť tarif, najprv zrušte aktuálne predplatné.'
                    }, status=400)

            price_id = PLAN_PRICES[requested_plan]

            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{'price': price_id, 'quantity': 1}],
                'mode': 'subscription',
                'success_url': settings.DOMAIN_URL + '/dashboard/?success=true&session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': settings.DOMAIN_URL + '/pricing/?canceled=true',
                'client_reference_id': str(request.user.id),
                # сохраняем, какой именно тариф покупали — прочитаем это в вебхуке
                'metadata': {'plan': requested_plan},
            }

            # Триал даём только если юзер им ещё не пользовался
            if not request.user.has_used_trial:
                session_params['subscription_data'] = {'trial_period_days': 3}

            checkout_session = stripe.checkout.Session.create(**session_params)
            return JsonResponse({'checkout_url': checkout_session.url})

        except stripe.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)  # Неверный формат данных
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        user_id = session.client_reference_id
        stripe_customer_id = session.customer
        stripe_subscription_id = session.subscription

        metadata = getattr(session, 'metadata', None)
        purchased_plan = getattr(metadata, 'plan', 'pro') if metadata else 'pro'

        print('DEBUG: user_id =', user_id, 'plan =', purchased_plan)

        try:
            user = Profile.objects.get(id=user_id)
            sub, created = UserSubscription.objects.get_or_create(user=user)
            sub.stripe_customer_id = stripe_customer_id
            sub.stripe_subscription_id = stripe_subscription_id
            sub.is_active = True
            sub.save()

            # Проверяем ДО того, как перезапишем has_used_trial
            if created or not user.has_used_trial:
                user.end_at = timezone.now() + timedelta(days=3)
            else:
                user.end_at = timezone.now() + timedelta(days=30)

            user.plan = purchased_plan
            user.has_used_trial = True
            user.start_at = timezone.now()
            user.save()

            print('DEBUG: успешно обновили юзера', user.email, '→', user.plan)
        except Profile.DoesNotExist:
            print('DEBUG: юзер с id', user_id, 'НЕ НАЙДЕН в базе')

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        stripe_subscription_id = None
        parent = getattr(invoice, 'parent', None)
        if parent and getattr(parent, 'subscription_details', None):
            stripe_subscription_id = parent.subscription_details.subscription

        if stripe_subscription_id:
            try:
                sub = UserSubscription.objects.get(
                    stripe_subscription_id=stripe_subscription_id
                )
                sub.is_active = True
                sub.save()
            except UserSubscription.DoesNotExist:
                pass

    # Пользователь отменил подписку или не удалось списать оплату (доступ нужно закрыть)
    elif event['type'] == 'customer.subscription.deleted':
        session = event['data']['object']
        stripe_subscription_id = session.id
        try:
            sub = UserSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            sub.is_active = False  # Забираем доступ
            sub.save()
        except UserSubscription.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
def dashboard_view(request):
    sub, created = UserSubscription.objects.get_or_create(user=request.user)
    return render(request, 'payment/dashboard.html', {'subscription': sub})