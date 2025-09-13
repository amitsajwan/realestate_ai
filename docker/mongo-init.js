// MongoDB initialization script for production
db = db.getSiblingDB('real_estate_platform');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'password_hash', 'created_at'],
      properties: {
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        },
        password_hash: {
          bsonType: 'string'
        },
        created_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('properties', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'price', 'agent_id', 'created_at'],
      properties: {
        title: {
          bsonType: 'string',
          minLength: 1,
          maxLength: 200
        },
        price: {
          bsonType: 'number',
          minimum: 0
        },
        agent_id: {
          bsonType: 'string'
        },
        created_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('agent_public_profiles');
db.createCollection('publishing_history');
db.createCollection('agent_language_preferences');

// Create indexes for performance
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'created_at': 1 });

db.properties.createIndex({ 'agent_id': 1 });
db.properties.createIndex({ 'publishing_status': 1 });
db.properties.createIndex({ 'created_at': 1 });
db.properties.createIndex({ 'price': 1 });
db.properties.createIndex({ 'location': 'text', 'title': 'text', 'description': 'text' });

db.agent_public_profiles.createIndex({ 'agent_id': 1 }, { unique: true });
db.agent_public_profiles.createIndex({ 'slug': 1 }, { unique: true });

db.publishing_history.createIndex({ 'property_id': 1 });
db.publishing_history.createIndex({ 'created_at': 1 });

db.agent_language_preferences.createIndex({ 'agent_id': 1 }, { unique: true });

print('Database initialized successfully');