from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..db import SessionLocal, UserProfile, UserHistory, DeviceActivity
from social_django.models import UserSocialAuth
from .github_utils import create_profile_from_github
import json
  
@login_required
def dashboard_view(request):
    db = SessionLocal()
    try:
        user_profile = db.query(UserProfile).filter_by(username=request.user.username).first()
        
        # Обработка GitHub пользователя
        if not user_profile:
            user_profile = handle_github_user(request, db)
            if not user_profile:
                return redirect('login')

        # Получение данных для отображения
        context = prepare_dashboard_context(user_profile, db, request)
        if context:
            return render(request, 'login/dashboard.html', context)
    finally:
        db.close()
    
    messages.error(request, 'Профиль пользователя не найден')
    return redirect('login')

def handle_github_user(request, db):
    try:
        github_login = request.user.social_auth.get(provider='github')
        if create_profile_from_github(request.user, db):
            return db.query(UserProfile).filter_by(username=request.user.username).first()
        messages.error(request, 'Ошибка при создании профиля')
    except UserSocialAuth.DoesNotExist:
        pass
    return None

def prepare_dashboard_context(user_profile, db, request):
    """Подготавливает контекст для отображения в dashboard"""
    if not user_profile:
        return None

    try:
        # Получение GitHub данных
        github_login = request.user.social_auth.get(provider='github')
        is_github_user = True
        github_data = github_login.extra_data
    except (UserSocialAuth.DoesNotExist, AttributeError):
        is_github_user = False
        github_data = None

    try:
        # Получение истории входов
        user_history = db.query(UserHistory).filter_by(unique_id=user_profile.unique_id).first()
        login_history = json.loads(user_history.login_history) if user_history else []

        # Получение активных устройств
        devices = db.query(DeviceActivity).filter_by(user_id=user_profile.id).all()

        return {
            'user_profile': user_profile,
            'login_history': login_history,
            'devices': devices,
            'is_github_user': is_github_user,
            'github_data': github_data
        }
    except Exception as e:
        messages.error(request, f'Ошибка при загрузке данных: {str(e)}')
        return None