from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView,
    UserViewSet, DeviceViewSet, MediaViewSet,
    PlaylistViewSet, ScheduleViewSet, DeviceLogViewSet, CurrentUserView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'users', UserViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'media', MediaViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'logs', DeviceLogViewSet, basename='logs')

urlpatterns = [
    path('', include(router.urls)),
    # path('playlists/<int:playlist_id>/<int:content_id>/', PlaylistViewSet.as_view(), name='playlist-content'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
]