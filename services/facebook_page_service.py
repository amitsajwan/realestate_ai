from services.mongo_client import db

class FacebookPageService:
    @staticmethod
    def save_page(user_id: str, page_id: str, page_name: str, access_token: str):
        doc = {
            'user_id': user_id,
            'page_id': page_id,
            'page_name': page_name,
            'access_token': access_token
        }
        db.facebook_pages.insert_one(doc)
        return doc

    @staticmethod
    def get_pages(user_id: str):
        return list(db.facebook_pages.find({'user_id': user_id}))
