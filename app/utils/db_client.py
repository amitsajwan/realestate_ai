from app.core.database import get_database

def get_db_client():
	"""Provide a synchronous-like database handle backed by AsyncIOMotor.

	This returns the database object created in app.core.database.connect_to_mongo().
	It matches the expected interface used by onboarding service (collection access with .find_one/.insert_one).
	"""
	return get_database()

