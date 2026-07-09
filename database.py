from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, text, inspect as sa_inspect
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./payevery_v2.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String, index=True)
    username      = Column(String, unique=True, index=True)
    phone         = Column(String, unique=True, index=True)
    password_hash = Column(String)
    pin_hash      = Column(String)
    bkash_balance = Column(Float, default=0.0)
    nagad_balance = Column(Float, default=0.0)

class VirtualCard(Base):
    __tablename__ = "virtual_cards"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"))
    card_number = Column(String, unique=True, index=True)
    status      = Column(String, default="ACTIVE")

class Transaction(Base):
    __tablename__ = "transactions"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    amount     = Column(Float)
    amount_usd = Column(Float, default=0.0)
    currency   = Column(String, default="BDT")
    merchant   = Column(String)
    status     = Column(String, default="SUCCESS")
    date       = Column(Date, default=datetime.date.today)
    tx_type    = Column(String, default="SINGLE")  # SINGLE or SQUAD

class SquadPool(Base):
    __tablename__ = "squad_pools"
    id             = Column(Integer, primary_key=True, index=True)
    pool_code      = Column(String, unique=True, index=True)
    leader_id      = Column(Integer, ForeignKey("users.id"))
    target_url     = Column(String)
    total_amount   = Column(Float)   # total amount in currency
    currency       = Column(String, default="USD")
    total_bdt      = Column(Float)   # total in BDT
    collected_bdt  = Column(Float, default=0.0)
    status         = Column(String, default="OPEN")  # OPEN, FUNDED, COMPLETED
    date           = Column(Date, default=datetime.date.today)
    description    = Column(String, default="")
    virtual_card   = Column(String, default="")
    expiry         = Column(String, default="")
    cvv            = Column(String, default="")

class SquadContribution(Base):
    __tablename__ = "squad_contributions"
    id          = Column(Integer, primary_key=True, index=True)
    pool_id     = Column(Integer, ForeignKey("squad_pools.id"))
    user_id     = Column(Integer, ForeignKey("users.id"))
    amount_bdt  = Column(Float)
    username    = Column(String)
    paid_at     = Column(Date, default=datetime.date.today)

Base.metadata.create_all(bind=engine)

# Auto-migrate: add missing columns without dropping data
with engine.connect() as conn:
    tx_cols = [c["name"] for c in sa_inspect(engine).get_columns("transactions")]
    if "currency" not in tx_cols:
        conn.execute(text("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT 'BDT'"))
        conn.commit()
    if "tx_type" not in tx_cols:
        conn.execute(text("ALTER TABLE transactions ADD COLUMN tx_type TEXT DEFAULT 'SINGLE'"))
        conn.commit()

print("Database ready.")