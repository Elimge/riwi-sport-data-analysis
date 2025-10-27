# src/db/database.py

import os
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """
    Create and return a SQLAlchemy engine using database credentials from environment variables.
    """

    try:
        # Construct the database URL
        db_url = (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )

        # Create the SQLAlchemy engine
        engine = create_engine(db_url)

        # Test the connection
        with engine.connect() as connection:
            print("Database connection established successfully.")
        return engine
    
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
    
# Example usage
if __name__ == "__main__":
    engine = get_engine()