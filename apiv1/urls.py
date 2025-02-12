from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('completeProfile/', CompeteProfileView.as_view(), name='completeProfile'),
    path('startupCheck/', StartupCheckView.as_view(), name='startupCheck'),
    path('getProfiles/', GetProfilesView.as_view(), name='getProfiles'),
    path('onSwipe/', OnSwipeActionView.as_view(), name='onSwipe'),
    path('getSelfProfile/', GetSelfProfileView.as_view(), name='getSelfProfile'),
    path('createChatRoom/', CreateChatRoomView.as_view(), name='createChatRoom'),
    path('directMessage/', DirectMessageView.as_view(), name='sendMessage'),
    path('getMessages/', GetMessagesView.as_view(), name='getMessages'),
    path('getSwipedOnSelf/', GetSwipedOnSelf.as_view(), name='getSwipedOnSelf'),
]
