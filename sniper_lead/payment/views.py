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

@method_decorator(login_required, name='dispatch')
class CreateCheckoutSessionView(View):

    def post(self, request, *args, **kwargs):
        try:
            price_id = 'price_1UCDEH4GOC7xoKdSCWnxT3MC'

            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{'price': price_id, 'quantity': 1}],
                'mode': 'subscription',
                'success_url': settings.DOMAIN_URL + '/dashboard/?success=true&session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': settings.DOMAIN_URL + '/pricing/?canceled=true',
                'client_reference_id': str(request.user.id),
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

        print('DEBUG: user_id =', user_id)  # ← добавь эту строку

        try:
            user = Profile.objects.get(id=user_id)
            sub, created = UserSubscription.objects.get_or_create(user=user)
            sub.stripe_customer_id = stripe_customer_id
            sub.stripe_subscription_id = stripe_subscription_id
            sub.is_active = True
            sub.save()
            user.has_used_trial = True
            user.plan = 'trial/pro'
            user.save()
            print('DEBUG: успешно обновили юзера', user.email)  # ← и эту
        except Profile.DoesNotExist:
            print('DEBUG: юзер с id', user_id, 'НЕ НАЙДЕН в базе')  # ← и эту

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