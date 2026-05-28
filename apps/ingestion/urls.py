from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ingestion.views import DataSourceViewSet, ActivityRecordViewSet
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
import json

router = DefaultRouter()
router.register('sources', DataSourceViewSet, basename='source')
router.register('records', ActivityRecordViewSet, basename='record')

# Token-based authentication APIs (works across different domains)

@api_view(['GET'])
@permission_classes([AllowAny])
def login_status_api(request):
    """Returns current authentication status based on token."""
    if request.user and request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "username": request.user.username,
            "email": request.user.email
        })
    return JsonResponse({"authenticated": False})

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Token login endpoint. Accepts {"username": "...", "password": "..."}.
    Returns an auth token on success.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return JsonResponse({"error": "Username and password are required"}, status=400)

    # If the user typed an email address, lookup their username
    if '@' in username:
        try:
            from django.contrib.auth.models import User
            user_obj = User.objects.get(email=username)
            username = user_obj.username
        except User.DoesNotExist:
            pass

    user = authenticate(request, username=username, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse({
            "authenticated": True,
            "username": user.username,
            "email": user.email,
            "token": token.key,
        })
    else:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """Deletes the user's auth token, effectively logging them out."""
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return JsonResponse({"detail": "Logged out successfully"})

urlpatterns = [
    path('', include(router.urls)),
    path('auth/status/', login_status_api),
    path('auth/login/', login_api),
    path('auth/logout/', logout_api),
]

