import json

from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from random import randint
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMessage




# Create your views here.
class SignUpView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            verification = self.emailVerification(request)
            cache.set(f'data_{request.data["email"]}', request.data, 600)
            return Response({"message": "Verification code Sent"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def emailVerification(self, request):
        verificationCode = randint(100000, 999999)
        cache.set(f"verificationCode_{request.data['email']}", verificationCode, 600)
        print(verificationCode, f"sent to {request.data['email']} and will expire in 10 minutes")
        #EmailMessage("Verification Code", f"Your verification code is: {verificationCode}", to=[request.data['email']]).send()
        return verificationCode


class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        code = cache.get(f'verificationCode_{request.data['email']}')

        recievedCode = int(request.data.get('verificationCode'))

        if recievedCode != code:
            return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        data = cache.get(f'data_{request.data["email"]}')
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(email=request.data['email'])
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({"refresh": str(refresh), "access": str(access)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({
                "refresh": str(refresh),
                "access": str(access),
                "isComplete" : user.profileCompleted
            }, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompeteProfileView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    serializer_class = CompleteProfileSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class StartupCheckView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({"profileCompleted": user.profileCompleted}, status=status.HTTP_200_OK)


class GetProfilesView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReturnUserSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        user = request.user
        userPoints = user.points
        responseItems = []
        updateHandle = User.objects.filter(id=user.id)
        if int(request.data.get('amount')) == 4:
            print("reset")
            updateHandle.update(temporarySent=[])
        profiles = (User.objects.filter(
            profileCompleted=True,
            points__gte=userPoints - 150,
            points__lte=userPoints + 150,
            gender__in=user.genderPreferences, )
                    .exclude(id=user.id).exclude(id__in=user.profilesAcceptedId).exclude(id__in=user.profilesRejectedId).exclude(id__in=user.temporarySent)

        [:int(request.data.get('amount'))])

        profiles = ReturnUserSerializer(profiles, many=True).data
        temporaryCreator = (User.objects.get(id=user.id).temporarySent or [])
        for profile in profiles:
            temporaryCreator.append(profile['id'])
            profile['images'] = User.objects.get(id=profile['id']).images
            responseItems.append(profile)

        User.objects.filter(id=user.id).update(temporarySent=temporaryCreator)
        return Response({"profiles": responseItems}, status=status.HTTP_200_OK)


class OnSwipeActionView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        user = request.user
        swipedUser = User.objects.get(id=request.data.get('swipedUserId'))
        direction = request.data.get('direction')
        accepted_ids = user.profilesAcceptedId or []
        rejected_ids = user.profilesRejectedId or []
        response = {"message": "success"}
        if direction == 'like':
            if isinstance(accepted_ids, str):
                accepted_ids = eval(accepted_ids)

            accepted_ids.append(swipedUser.id)
            user.profilesAcceptedId = accepted_ids
            user.points = user.points - 2
            swipedUser.points = swipedUser.points + 5
            if user.id in swipedUser.profilesAcceptedId:
                response = {"message": "Match"}
        elif direction == 'dislike':
            if isinstance(rejected_ids, str):
                rejected_ids = eval(rejected_ids)

            rejected_ids.append(swipedUser.id)
            user.profilesRejectedId = rejected_ids
            user.points = user.points - 1
            swipedUser.points = swipedUser.points - 5

        # Save without triggering the image handling in save()
        User.objects.filter(id=user.id).update(
            profilesAcceptedId=user.profilesAcceptedId,
            profilesRejectedId=user.profilesRejectedId,
            points=user.points
        )

        User.objects.filter(id=swipedUser.id).update(
            points=swipedUser.points
        )
        return Response(response, status=status.HTTP_200_OK)


class GetSelfProfileView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteProfileSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        serializers = CompleteProfileSerializer(user)
        responseData = dict(serializers.data)
        responseData['images'] = user.images
        return Response(responseData, status=status.HTTP_200_OK)


class CreateChatRoomView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatRoomSerializer

    def post(self, request, *args, **kwargs):
        user1 = request.user
        user2 = get_object_or_404(User, id=request.data.get('userId'))
        conversation, created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)
        return Response({"message": "success", "roomId": conversation.id, "userId": user2.id, "selfUserId": user1.id, "selfUserName": user1.first_name, "userName": user2.first_name, "mainImage": user2.mainImage}, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        conversations = ChatRoom.objects.filter(user1=user.id) | ChatRoom.objects.filter(user2=user.id)
        serializer = ChatRoomSerializer(conversations, many=True)
        otherUsers = []
        for chatRooms in serializer.data:
            if chatRooms['user1'] == user.id:
                otherUserObject = User.objects.get(id=chatRooms['user2'])
            else:
                otherUserObject = User.objects.get(id=chatRooms['user1'])
            otherUserData = {"name": f"{otherUserObject.first_name} {otherUserObject.last_name}",
                             "userId": otherUserObject.id, "selfName": f"{user.first_name} {user.last_name}",
                             "selfUserId": user.id, "mainImage": otherUserObject.mainImage, "roomId": chatRooms['id']}
            otherUsers.append(otherUserData)
        return Response(otherUsers, status=status.HTTP_200_OK)


class DirectMessageView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DirectMessageSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        conversation = get_object_or_404(ChatRoom, id=request.data.get('chatRoomId'))
        serializer = DirectMessageSerializer(
            data={"content": request.data.get('content'), "sender": user.id, "room": conversation.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetMessagesView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DirectMessageSerializer

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(ChatRoom, id=request.data.get('chatRoomId'))
        messages = DirectMessage.objects.filter(room=conversation.id)
        serializer = DirectMessageSerializer(messages, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class GetSwipedOnSelf(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SelfSwipedSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        swipedOn = User.objects.filter(profilesAcceptedId__contains=[user.id]).exclude(id__in=user.profilesAcceptedId).exclude(id__in=user.profilesRejectedId)
        serializer = SelfSwipedSerializer(swipedOn, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)