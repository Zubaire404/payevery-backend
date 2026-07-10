from database import SessionLocal, User

def seed_data():
    
    db = SessionLocal()
    
    try:
        # Checkings
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️ Data already exists in the database. Skipping insertion to prevent duplicates.")
            return

        # Users ID
        users = [
            User(name="Sohel", bkash_balance=50000.0, nagad_balance=50000.0),      
            User(name="Rifat", bkash_balance=50000.0, nagad_balance=50000.0),    
            User(name="Hasan", bkash_balance=50000.0, nagad_balance=50000.0),
            User(name="Ratul", bkash_balance=50000.0, nagad_balance=50000.0)       
        ]

        
        db.add_all(users)
        db.commit()
        
        print("✅ Successfully seeded the database with 4 dummy users!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        db.rollback() # কোনো এরর হলে ডাটাবেসকে আগের অবস্থায় ফিরিয়ে নেওয়া
    finally:
        db.close() # কাজ শেষে সেশন বন্ধ করে দেওয়া (মেমোরি বাঁচানোর জন্য)

# স্ক্রিপ্টটি রান করা হলে ফাংশনটি কল হবে
if __name__ == "__main__":
    seed_data()