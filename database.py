from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./payevery.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bkash_balance = Column(Float, default=0.0)
    nagad_balance = Column(Float, default=0.0)

class VirtualCard(Base):
    __tablename__ = "virtual_cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_number = Column(String, unique=True, index=True)
    status = Column(String, default="ACTIVE")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    amount_usd = Column(Float, default=0.0) # 🔴 NEW: লিমিট হিসেবের জন্য ডলার অ্যামাউন্ট
    merchant = Column(String)
    status = Column(String, default="SUCCESS")
    date = Column(Date, default=datetime.date.today) # 🔴 NEW: প্রতিদিনের হিসাব রাখার জন্য তারিখ

Base.metadata.create_all(bind=engine)
print("Database and Tables created successfully with Date tracking!")