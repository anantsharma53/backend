from rest_framework import serializers
from .models import User, Device, Media, Playlist, Schedule, DeviceLog
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token
    # def validate(self, attrs):
    #     data = super().validate(attrs)
    #     # Include user data in the response
    #     data['user'] = {
    #         'id': self.user.id,
    #         'username': self.user.username,
    #         'email': self.user.email,
    #         # Add other fields as needed
    #     }
    #     return data
    def validate(self, attrs):
        data = super().validate(attrs)
        data['status'] = 'success'
        data['user'] = UserSerializer(self.user).data
        return data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'company', 'phone','is_staff']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            company=validated_data.get('company', ''),
            phone=validated_data.get('phone', ''),
        )
        return user

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ['owner', 'last_active']

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'
        read_only_fields = ['owner', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.file:
            representation['file_url'] = instance.file.url
        if instance.thumbnail:
            representation['thumbnail_url'] = instance.thumbnail.url
        return representation

class PlaylistSerializer(serializers.ModelSerializer):
    items = MediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class ScheduleSerializer(serializers.ModelSerializer):
    playlist = PlaylistSerializer(read_only=True)
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = Schedule
        fields = '__all__'

class DeviceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceLog
        fields = '__all__'