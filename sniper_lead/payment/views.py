import stripe
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserSubscription

stripe.api_key = settings.STRIPE_SECRET_KEY

@method_decorator(login_required, name='dispatch')
class CreateCheckoutSessionView(View):

    def post(self, request, *args, **kwargs):
        try:
            price_id = 'price_1UCDEH4GOC7xoKdSCWnxT3MC'

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.DOMAIN_URL + '/dashboard/?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.DOMAIN_URL + '/pricing/?canceled=true',
                client_reference_id=str(request.user.id)

            )
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
            payload,sig_header,settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)  # Неверный формат данных
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        user_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')

        try:
            user = User.objects.get(id=user_id)
            sub, created = UserSubscription.objects.get_or_create(user=user)
            sub.stripe_customer_id = stripe_customer_id
            sub.stripe_subscription_id = stripe_subscription_id
            sub.is_active = True  # Даем доступ к SniperLead!
            sub.save()
        except User.DoesNotExist:
            pass

    elif event['type'] == 'invoice.payment_succeeded':
        session = event['data']['object']
        stripe_subscription_id = session.get('subscription')
        try:
            sub = UserSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            sub.is_active = True
            sub.save()
        except UserSubscription.DoesNotExist:
            pass

        # 3. Пользователь отменил подписку или кончилась карта (доступ нужно закрыть)
    elif event['type'] == 'customer.subscription.deleted':
        session = event['data']['object']
        stripe_subscription_id = session.get('id')
        try:
            sub = UserSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            sub.is_active = False  # Забираем доступ
            sub.save()
        except UserSubscription.DoesNotExist:
            pass

    return HttpResponse(status=200)