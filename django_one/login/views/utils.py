from datetime import datetime, timedelta
import requests
import json
from ..db import LoginAttempt, UserHistory, DeviceActivity

def create_new_login_attempt(ip_address, now, db):
    """Создает новую запись попытки входа"""
    login_attempt = LoginAttempt(
        ip_address=ip_address,
        attempt_time=now,
        attempt_count=0
    )
    db.add(login_attempt)
    return login_attempt

def validate_login_attempt(login_attempt, now, db):
    """Проверяет и обновляет попытку входа"""
    if login_attempt.blocked_until and login_attempt.blocked_until > now:
        remaining_time = login_attempt.blocked_until - now
        minutes = int(remaining_time.total_seconds() / 60)
        return False, f"Слишком много попыток входа. Попробуйте через {minutes} минут."

    if login_attempt.attempt_time and (now - login_attempt.attempt_time) > timedelta(minutes=30):
        login_attempt.attempt_count = 0

    login_attempt.attempt_time = now
    login_attempt.attempt_count += 1

    if login_attempt.attempt_count >= 5:
        login_attempt.blocked_until = now + timedelta(minutes=30)
        db.commit()
        return False, "Слишком много попыток входа. Аккаунт заблокирован на 30 минут."

    db.commit()
    return True, None

def check_ip_attempts(ip_address, db):
    """Проверяет попытки входа с IP-адреса"""
    now = datetime.now()
    login_attempt = db.query(LoginAttempt).filter_by(ip_address=ip_address).first()

    if not login_attempt:
        login_attempt = create_new_login_attempt(ip_address, now, db)
    
    return validate_login_attempt(login_attempt, now, db)

def get_geolocation(ip_address):
    """Получает геолокацию по IP адресу"""
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')}"
    except requests.RequestException:
        return "Unknown"

def update_login_history(db, user_profile, ip_address, device_info, geolocation, current_time):
    """Обновляет историю входов пользователя"""
    try:
        user_history = db.query(UserHistory).filter_by(unique_id=user_profile.unique_id).first()
        if user_history:
            try:
                login_history = json.loads(user_history.login_history)
            except json.JSONDecodeError:
                login_history = []
                
            login_history.append({
                'timestamp': current_time.isoformat(),
                'ip_address': ip_address,
                'device_info': device_info,
                'geolocation': geolocation
            })
            user_history.login_history = json.dumps(login_history)
            user_history.last_login = current_time
    except Exception as e:
        db.rollback()
        raise e

def update_device_activity(db, user_profile, device_info, current_time, geolocation):
    """Обновляет активность устройства"""
    device_activity = (
        db.query(DeviceActivity)
        .filter_by(user_id=user_profile.id, device_info=device_info)
        .first()
    )
    
    if device_activity:
        device_activity.last_active = current_time
        device_activity.geolocation = geolocation
    else:
        new_device = DeviceActivity(
            user_id=user_profile.id,
            device_info=device_info,
            last_active=current_time,
            geolocation=geolocation
        )
        db.add(new_device) 