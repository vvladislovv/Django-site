from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, date
from ..db import SessionLocal, UserProfile, UserHistory, DeviceActivity
from .utils import check_ip_attempts, get_geolocation, update_login_history, update_device_activity
from .github_utils import create_user_history, create_device_activity
import uuid
import json

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']
        ip_address = request.META.get('REMOTE_ADDR')
        
        db = SessionLocal()
        try:
            # Проверка попыток входа
            can_attempt, error_message = check_ip_attempts(ip_address, db)
            if not can_attempt:
                messages.error(request, error_message)
                return render(request, "login/login.html")

            # Аутентификация
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = username_or_email

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                current_time = datetime.now()
                device_info = request.META.get('HTTP_USER_AGENT', 'Unknown')
                geolocation = get_geolocation(ip_address)

                # Обновление профиля
                try:
                    user_profile = db.query(UserProfile).filter_by(email=username_or_email).first()
                    if user_profile:
                        user_profile.last_login = current_time
                        user_profile.ip_address = ip_address
                        user_profile.device_info = device_info
                        user_profile.geolocation = geolocation

                        update_login_history(db, user_profile, ip_address, device_info, geolocation, current_time)
                        update_device_activity(db, user_profile, device_info, current_time, geolocation)

                        db.commit()
                except Exception:
                    db.rollback()

                return redirect('dashboard')
            else:
                messages.error(request, 'Неверные учетные данные!')
        finally:
            db.close()

    return render(request, "login/login.html")

def register_view(request):
    if request.method == 'POST':
        # Получение данных из формы
        form_data = {
            'name': request.POST['name'],
            'birth_date': date(
                int(request.POST['birth_year']),
                int(request.POST['birth_month']),
                int(request.POST['birth_day'])
            ),
            'email': request.POST['email'],
            'password': request.POST['password'],
            'confirm_password': request.POST['confirm_password']
        }

        # Валидация данных
        if not validate_registration_data(request, form_data):
            return render(request, 'login/register.html')

        # Создание пользователя
        try:
            user = create_django_user(form_data)
            profile_data = collect_profile_data(request, user)
            
            # Передаем profile_data в create_user_profile
            if create_user_profile(SessionLocal(), profile_data):  # Убедитесь, что передаете сессию
                user = authenticate(request, username=form_data['name'], password=form_data['password'])
                if user:
                    login(request, user)
                    return redirect('dashboard')
            else:
                user.delete()
                messages.error(request, 'Ошибка при регистрации. Попробуйте еще раз.')
        except Exception as e:
            messages.error(request, f'Ошибка при регистрации: {str(e)}')

        return redirect('login')

    # GET запрос
    context = prepare_registration_context()
    return render(request, 'login/register.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

# Вспомогательные функции для регистрации
def validate_registration_data(request, data):
    """Проверяет данные регистрации"""
    if not (1900 <= data['birth_date'].year <= datetime.now().year):
        messages.error(request, 'Пожалуйста, выберите корректный год рождения.')
        return False
    if data['password'] != data['confirm_password']:
        messages.error(request, 'Пароли не совпадают!')
        return False
    if User.objects.filter(username=data['name']).exists():
        messages.error(request, 'Пользователь с таким именем уже существует!')
        return False
    if User.objects.filter(email=data['email']).exists():
        messages.error(request, 'Пользователь с такой почтой уже существует!')
        return False
    return True

def collect_profile_data(request, user):
    """Собирает данные для профиля пользователя"""
    return {
        'username': user.username,
        'email': user.email,
        'password': user.password,
        'birth_date': request.POST.get('birth_date'),
        'ip_address': request.META.get('REMOTE_ADDR'),
        'device_info': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'unique_id': str(uuid.uuid4()),
        'current_time': datetime.now(),
        'geolocation': get_geolocation(request.META.get('REMOTE_ADDR'))
    }

def create_user_profile(db, profile_data):
    """Создает профиль пользователя и связанные записи"""
    try:
        user_profile = UserProfile(
            username=profile_data['username'],
            email=profile_data['email'],
            birth_date=profile_data.get('birth_date'),
            ip_address=profile_data['ip_address'],
            unique_id=profile_data['unique_id'],
            geolocation=profile_data['geolocation'],
            device_info=profile_data['device_info'],
            last_login=profile_data['current_time']
        )
        db.add(user_profile)
        db.flush()

        # Создаем историю и активность устройства
        create_user_history(db, profile_data)
        create_device_activity(db, user_profile.id, profile_data)

        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def create_django_user(data):
    """Создает пользователя с зашифрованным паролем"""
    return User.objects.create_user(
        username=data['name'],
        email=data['email'],
        password=data['password']  # Пароль будет автоматически зашифрован
    )

def prepare_registration_context():
    current_year = datetime.now().year
    months = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]
    return {
        'years': list(range(1930, current_year + 1)),
        'days': list(range(1, 32)),
        'months': [(i, month) for i, month in enumerate(months, start=1)]
    }