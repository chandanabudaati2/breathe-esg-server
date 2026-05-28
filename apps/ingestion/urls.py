from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ingestion.views import DataSourceViewSet, ActivityRecordViewSet
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
import json

router = DefaultRouter()
router.register('sources', DataSourceViewSet, basename='source')
router.register('records', ActivityRecordViewSet, basename='record')

# JSON-based authentication APIs (replaces DRF browsable HTML login)

def login_status_api(request):
    """Returns current authentication status as JSON."""
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "username": request.user.username,
            "email": request.user.email
        })
    return JsonResponse({"authenticated": False})

@ensure_csrf_cookie
def get_csrf_token(request):
    """Sets the CSRF cookie for the frontend to read."""
    return JsonResponse({"detail": "CSRF cookie set"})

@require_POST
def login_api(request):
    """
    JSON login endpoint. Accepts {"username": "...", "password": "..."} as JSON body.
    Creates a Django session on success.
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
        login(request, user)
        return JsonResponse({
            "authenticated": True,
            "username": user.username,
            "email": user.email
        })
    else:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

@require_POST
def logout_api(request):
    """JSON logout endpoint. Destroys the Django session."""
    logout(request)
    return JsonResponse({"detail": "Logged out successfully"})

urlpatterns = [
    path('', include(router.urls)),
    path('auth/status/', login_status_api),
    path('auth/csrf/', get_csrf_token),
    path('auth/login/', login_api),
    path('auth/logout/', logout_api),
]
