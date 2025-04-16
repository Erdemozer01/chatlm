from django.urls import path
from .views import ask

urlpatterns = [
    path('', ask, name='ask_chat'),
]