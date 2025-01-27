from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship  # Import missing relationship

# Database configuration
DATABASE_URL = "sqlite:///db.sqlite3"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Хешированный пароль Django
    birth_date = Column(Date)
    ip_address = Column(String)
    unique_id = Column(String, unique=True)
    geolocation = Column(String)
    device_info = Column(String)
    last_login = Column(DateTime)

    def __repr__(self):
        return (f"<UserProfile(username={self.username}, email={self.email}, "
                f"birth_date={self.birth_date}, ip_address={self.ip_address}, "
                f"unique_id={self.unique_id})>")


class UserHistory(Base):
    __tablename__ = "UserHistory"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True)
    last_login = Column(DateTime)
    device_info = Column(String)
    registration_date = Column(DateTime)  # Дата регистрации
    login_history = Column(String)  # История входа в формате JSON

    def __repr__(self):
        return (f"<UserHistory(unique_id={self.unique_id}, "
                f"last_login={self.last_login}, registration_date={self.registration_date}, "
                f"login_history={self.login_history}, device_info={self.device_info})>")


class DeviceActivity(Base):
    __tablename__ = "device_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user_profiles.id'), index=True)  # Foreign key to UserProfile
    device_info = Column(String)  # Information about the device
    last_active = Column(DateTime)  # Last active time
    geolocation = Column(String)  # User's geolocation

    user_profile = relationship("UserProfile", back_populates="devices")

    def __repr__(self):
        return (f"<DeviceActivity(user_id={self.user_id}, device_info={self.device_info}, "
                f"last_active={self.last_active}, geolocation={self.geolocation})>")

UserProfile.devices = relationship("DeviceActivity", order_by=DeviceActivity.id, back_populates="user_profile")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String)
    attempt_time = Column(DateTime)
    is_successful = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)
    blocked_until = Column(DateTime, nullable=True)

    def __repr__(self):
        return (f"<LoginAttempt(ip={self.ip_address}, "
                f"attempts={self.attempt_count}, "
                f"blocked_until={self.blocked_until})>")


# Create the database tables
def init_db():
    Base.metadata.drop_all(bind=engine)  # Удаляем существующие таблицы
    Base.metadata.create_all(bind=engine)  # Создаем таблицы заново 