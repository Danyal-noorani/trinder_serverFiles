from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import default_storage


# Create your models here.



class UserProfile(AbstractUser):
    gender = models.CharField(max_length=30, blank=True)
    age = models.IntegerField(blank=True, null=True)
    studyYear = models.CharField(blank=True, null=True)
    degree = models.CharField(max_length=30, blank=True, null=True)
    major = models.CharField(max_length=30, blank=True, null=True)
    about = models.CharField(max_length=1000, blank=True, null=True)
    hobbiesAndInterests = ArrayField(models.CharField(max_length=30), default=list)
    points = models.IntegerField(default=0)
    profileCompleted = models.BooleanField(default=False)
    isErasmus = models.BooleanField(default=False)
    images = ArrayField(models.ImageField(), default=list)
    mainImage = models.CharField(max_length=1000, blank=True, null=True)
    lookingForPreferences = ArrayField(models.CharField(max_length=30), default=list)
    genderPreferences = ArrayField(models.CharField(max_length=30), default=list)
    studyYearPreferences = ArrayField(models.CharField(max_length=30), default=list)
    degreePreferences = ArrayField(models.CharField(max_length=30), default=list)
    profilesAcceptedId = ArrayField(models.IntegerField(), default=list)
    profilesRejectedId = ArrayField(models.IntegerField(), default=list)
    temporarySent = ArrayField(models.IntegerField(), default=list)

    def save(self, *args, **kwargs):
        tempImages = []
        print(self.images)
        for i, image in enumerate(self.images):
            if 'existing' in image.name:
                tempImages.append(image.name[8:].replace('|', '/'))
                continue
            if i == 0:
                self.mainImage = f'user_images/{self.username}_{self.id}/{image.name}'
            if isinstance(image, InMemoryUploadedFile) or isinstance(image,TemporaryUploadedFile):
                file_path = f'user_images/{self.username}_{self.id}/{image.name}'
                print(file_path)
                if not default_storage.exists(f'user_images/{self.username}_{self.id}/{image.name}'):
                    default_storage.save(file_path, image)
                tempImages.append(file_path)
        self.images = []
        print(tempImages)
        self.images= tempImages
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class ChatRoom(models.Model):
    user1 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']

class DirectMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    message = models.TextField()
    createdAt = models.DateTimeField()
    sentBy = models.CharField(max_length=100)
    reply_message = models.JSONField()
    reaction = models.JSONField()
    message_type = models.CharField(max_length=100, null=True)
    is_read = models.BooleanField(default=False)
    status = models.CharField(max_length=100, default='delivered')


