from django.urls import path
from . views import *

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('profile/', profile, name='profile'),
    path('logout/', logout, name='logout'),

    # Привязка Telegram
    path('telegram/generate-link/', generate_telegram_link, name='generate-telegram-link'),
    path('telegram/link-confirm/', telegram_link_confirm, name='telegram-link-confirm'),  # вызывает бот
    path('telegram/unlink/', telegram_unlink, name='telegram-unlink'),
]
