from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up the database connection
DATABASE_URI = 'mysql+pymysql://root:1060789Bmy!@127.0.0.1:3306/receipts'
engine = create_engine(DATABASE_URI)

# Create a session
Session = sessionmaker(bind=engine)

def restart_connection():
    pass

class DB():
    def write_query(self, query, values):
        session = Session()  # Create a new session
        try:
            # Execute the query
            result = session.execute(text(query), values)
            session.commit()  # Commit the transaction
            return result.lastrowid
        except Exception as e:
            print(f"An error occurred: {e}")
            session.rollback()  # Roll back the transaction on error
            return False
        finally:
            session.close()  # Close the session

    def read_query(self, query, values):
        results = []
        session = Session()  # Create a new session
        try:
            # Execute the query
            result = session.execute(text(query), values)
            results = result.fetchall()  # Fetch all results
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            session.close()  # Close the session

        return results