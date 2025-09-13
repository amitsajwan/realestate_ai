// MongoDB initialization script for development
db = db.getSiblingDB('real_estate_platform_dev');

// Create collections (no validation for development)
db.createCollection('users');
db.createCollection('properties');
db.createCollection('agent_public_profiles');
db.createCollection('publishing_history');
db.createCollection('agent_language_preferences');

// Create basic indexes
db.users.createIndex({ 'email': 1 });
db.properties.createIndex({ 'agent_id': 1 });
db.properties.createIndex({ 'publishing_status': 1 });
db.agent_public_profiles.createIndex({ 'agent_id': 1 });
db.agent_public_profiles.createIndex({ 'slug': 1 });

print('Development database initialized successfully');