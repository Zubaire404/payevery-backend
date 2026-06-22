from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# ১. ডাটাবেসের লোকেশন নির্ধারণ (এটি প্রজেক্ট ফোল্ডারে payevery.db নামে সেভ হবে)
SQLALCHEMY_DATABASE_URL = "sqlite:///./payevery.db"

# ২. ইঞ্জিন তৈরি (check_same_thread=False দেওয়া হয়েছে যাতে FastAPI-তে ক্র্যাশ না করে)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ৩. টেবিল ডিজাইন (ORM ক্লাসের মাধ্যমে)

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
    status = Column(String, default="ACTIVE")  # স্ট্যাটাস হবে ACTIVE বা DESTROYED

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    merchant = Column(String)
    status = Column(String, default="SUCCESS")

# ৪. কোড রান করার সাথে সাথে ডাটাবেস ও টেবিলগুলো তৈরি করার কমান্ড
Base.metadata.create_all(bind=engine)

print("Database and Tables created successfully for PayEvery!")