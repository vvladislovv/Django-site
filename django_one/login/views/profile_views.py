from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..db import SessionLocal, UserProfile

@login_required
def view_profiles(request):
    """Отображает профили пользователей"""
    db = SessionLocal()
    try:
        profiles = db.query(UserProfile).all()
        return render(request, 'login/view_profiles.html', {'profiles': profiles})
    finally:
        db.close() 