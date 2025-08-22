from services.mongo_client import db

class FacebookPostService:
    @staticmethod
    def save_post(user_id: str, page_id: str, post_id: str, message: str, image_url: str):
        doc = {
            'user_id': user_id,
            'page_id': page_id,
            'post_id': post_id,
            'message': message,
            'image_url': image_url
        }
        db.facebook_posts.insert_one(doc)
        return doc

    @staticmethod
    def get_posts(user_id: str, page_id: str):
        return list(db.facebook_posts.find({'user_id': user_id, 'page_id': page_id}))
