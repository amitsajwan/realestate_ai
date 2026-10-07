"""DEV/TEST ONLY: backdate a listing's freshness so the 'still available?' flow can be exercised.

  DATABASE_NAME=propertyai_final PYTHONPATH=. python scripts/dev_set_freshness.py <listing_id> <days_ago>
Refuses to run when ENVIRONMENT=production.
"""
import os
import sys
from datetime import datetime, timedelta

from pymongo import MongoClient

if os.environ.get("ENVIRONMENT") == "production":
    sys.exit("refusing to run in production")
listing_id, days = sys.argv[1], float(sys.argv[2])
url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
db = MongoClient(url)[os.environ.get("DATABASE_NAME", "propertyai")]
when = datetime.utcnow() - timedelta(days=days)
res = db.listings.update_one({"_id": listing_id}, {"$set": {"freshness_confirmed_at": when, "published_at": when}})
print("matched", res.matched_count)
