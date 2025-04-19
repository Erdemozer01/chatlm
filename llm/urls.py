from django.urls import path
from .views import ChatLmmView

urlpatterns = [
    path('', ChatLmmView, name='chat_lmm_view'),

]
