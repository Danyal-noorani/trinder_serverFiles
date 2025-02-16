import json

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate, get_user_model
from .models import *

User = get_user_model()


class ReturnUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'gender', 'age', 'studyYear', 'degree', 'about', 'major',
                  'hobbiesAndInterests', 'isErasmus', 'lookingForPreferences', 'mainImage','images']

class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password],
                                     style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['username'] = validated_data['email']
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            userExists = User.objects.filter(email=email).first()
            if userExists:
                user = authenticate(username=email, password=password)
                if not user:
                    raise serializers.ValidationError({"message": "Invalid password"})
                attrs['user'] = user
                return attrs
            raise serializers.ValidationError({"message": "Email doesn't exist"})



class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password],
                                     style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    class meta:
        model = UserProfile
        fields = ['email','password','password2','verificationCode']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        print("saved password as ", instance.password)
        return instance

class CompleteProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['gender', 'age', 'studyYear', 'major', 'degree', 'about', 'hobbiesAndInterests',
                  'lookingForPreferences',
                  'images', 'profileCompleted', 'genderPreferences', 'studyYearPreferences', 'degreePreferences',
                  'isErasmus','first_name','last_name','email']

    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            try:
                val = json.loads(val[0])
            except:
                pass
            setattr(instance, attr, val)
        instance.save()
        return instance

    def get_images(self, obj):
        # Assuming `images` is a list of file paths in the database
        if isinstance(obj.images, list):
            print([str(image) for image in obj.images])
            return [str(image) for image in obj.images]
        return obj.images


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'

class DirectMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectMessage
        fields = '__all__'

class SelfSwipedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'gender', 'age', 'studyYear', 'degree', 'about', 'major', 'hobbiesAndInterests', 'isErasmus', 'lookingForPreferences','first_name', 'last_name', 'mainImage']