from datetime import datetime
import uuid
import json
from ..db import UserProfile, UserHistory, DeviceActivity

def create_profile_from_github(user, db):
    """Создает профиль пользователя из данных GitHub"""
    try:
        # Проверяем, существует ли уже профиль
        existing_profile = db.query(UserProfile).filter_by(username=user.username).first()
        if existing_profile:
            return True

        github_login = user.social_auth.get(provider='github')
        profile_data = prepare_github_profile_data(user)
        
        # Создание профиля
        user_profile = create_user_profile(db, profile_data)
        if not user_profile:
            return False
        
        # Создание истории
        create_user_history(db, profile_data)
        
        # Создание активности устройства
        create_device_activity(db, user_profile.id, profile_data)

        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def prepare_github_profile_data(user):
    current_time = datetime.now()
    return {
        'username': user.username,
        'email': user.email,
        'password': user.password,
        'unique_id': str(uuid.uuid4()),
        'current_time': current_time,
        'ip_address': "Unknown",
        'device_info': "GitHub Registration",
        'geolocation': "Unknown"
    } 

def create_user_profile(db, profile_data):
    """Создает профиль пользователя"""
    user_profile = UserProfile(
        username=profile_data['username'],
        email=profile_data['email'],
        password=profile_data['password'],
        birth_date=None,
        ip_address=profile_data['ip_address'],
        unique_id=profile_data['unique_id'],
        geolocation=profile_data['geolocation'],
        device_info=profile_data['device_info'],
        last_login=profile_data['current_time']
    )
    db.add(user_profile)
    db.flush()
    return user_profile

def create_user_history(db, profile_data):
    """Создает историю пользователя"""
    user_history = UserHistory(
        unique_id=profile_data['unique_id'],
        last_login=profile_data['current_time'],
        device_info=profile_data['device_info'],
        registration_date=profile_data['current_time'],
        login_history=json.dumps([{
            'timestamp': profile_data['current_time'].isoformat(),
            'ip_address': profile_data['ip_address'],
            'device_info': profile_data['device_info'],
            'geolocation': profile_data['geolocation'],
            'provider': 'GitHub'
        }])
    )
    db.add(user_history)

def create_device_activity(db, user_id, profile_data):
    """Создает запись активности устройства"""
    device_activity = DeviceActivity(
        user_id=user_id,
        device_info=profile_data['device_info'],
        last_active=profile_data['current_time'],
        geolocation=profile_data['geolocation']
    )
    db.add(device_activity)