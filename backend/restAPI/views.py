from rest_framework import viewsets, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import User, Device, Media, Playlist, Schedule, DeviceLog
from .serializers import (
    UserSerializer, DeviceSerializer, MediaSerializer, 
    PlaylistSerializer, ScheduleSerializer, DeviceLogSerializer,
    CustomTokenObtainPairSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'status': 'success',
            'user': serializer.data
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'register']:
            return [AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Get token for the new user
        refresh = RefreshToken.for_user(user)
        data = {
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(data, status=status.HTTP_201_CREATED)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        device = self.get_object()
        device.last_active = timezone.now()
        device.save()
        
        # Log the check-in
        DeviceLog.objects.create(
            device=device,
            action='check_in',
            details={'ip': request.META.get('REMOTE_ADDR')}
        )
        
        # Get current schedule for this device
        now = timezone.now()
        schedules = Schedule.objects.filter(
            device=device,
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        ).order_by('-start_time')
        
        if schedules.exists():
            schedule = schedules.first()
            playlist_data = PlaylistSerializer(schedule.playlist).data
            return Response({
                'status': 'active',
                'playlist': playlist_data,
                'schedule_id': schedule.id
            })
        return Response({'status': 'idle'})

class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Media.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        playlist = self.get_object()
        media_id = request.data.get('media_id')
        media = get_object_or_404(Media, id=media_id, owner=request.user)
        playlist.items.add(media)
        return Response({'status': 'item added'})

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        playlist = self.get_object()
        media_id = request.data.get('media_id')
        media = get_object_or_404(Media, id=media_id, owner=request.user)
        playlist.items.remove(media)
        return Response({'status': 'item removed'})

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Schedule.objects.filter(playlist__owner=self.request.user)

    def perform_create(self, serializer):
        playlist = serializer.validated_data['playlist']
        if playlist.owner != self.request.user:
            raise PermissionDenied("You don't own this playlist")
        device = serializer.validated_data['device']
        if device.owner != self.request.user:
            raise PermissionDenied("You don't own this device")
        serializer.save()

class DeviceLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeviceLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        device_id = self.request.query_params.get('device_id')
        if device_id:
            device = get_object_or_404(Device, id=device_id, owner=self.request.user)
            return DeviceLog.objects.filter(device=device)
        return DeviceLog.objects.filter(device__owner=self.request.user)
