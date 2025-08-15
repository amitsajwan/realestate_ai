# Continuing the production CRM with API endpoints and additional pages

@app.post("/api/register")
async def register_user(request: Request):
    """Register new agent."""
    data = await request.json()
    
    # Hash password
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, phone, experience, areas, property_types, languages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['email'], password_hash, data['firstName'], data['lastName'],
            data['phone'], data['experience'], data['areas'], data['propertyTypes'], data['languages']
        ))
        
        conn.commit()
        return {"message": "Registration successful"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

@app.post("/api/login")
async def login_user(request: Request):
    """Login agent."""
    data = await request.json()
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, email, first_name, last_name, phone, experience, areas, property_types, languages, facebook_connected
        FROM users WHERE email = ? AND password_hash = ?
    ''', (data['email'], password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token_data = {
        "user_id": user[0],
        "email": user[1],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    
    return {
        "token": token,
        "user": {
            "id": user[0],
            "email": user[1],
            "firstName": user[2],
            "lastName": user[3],
            "phone": user[4],
            "experience": user[5],
            "areas": user[6],
            "propertyTypes": user[7],
            "languages": user[8],
            "facebookConnected": bool(user[9])
        }
    }

@app.get("/api/leads")
async def get_leads(payload: dict = Depends(verify_token)):
    """Get all leads for agent."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, email, phone, location, budget, property_type, source, status, score, notes, created_at
        FROM leads WHERE agent_id = ? ORDER BY created_at DESC
    ''', (payload['user_id'],))
    
    leads = cursor.fetchall()
    conn.close()
    
    return [dict(lead) for lead in leads]

@app.post("/api/leads")
async def create_lead(request: Request, payload: dict = Depends(verify_token)):
    """Create new lead."""
    data = await request.json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO leads (agent_id, name, email, phone, location, budget, property_type, source, status, score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payload['user_id'], data['name'], data.get('email'), data['phone'],
        data.get('location'), data.get('budget'), data.get('property_type'),
        data.get('source', 'manual'), data.get('status', 'new'),
        data.get('score', 75), data.get('notes', '')
    ))
    
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    
    return {"id": lead_id, "message": "Lead created successfully"}

@app.get("/api/properties")
async def get_properties(payload: dict = Depends(verify_token)):
    """Get all properties for agent."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status, created_at
        FROM properties WHERE agent_id = ? ORDER BY created_at DESC
    ''', (payload['user_id'],))
    
    properties = cursor.fetchall()
    conn.close()
    
    return [dict(prop) for prop in properties]

@app.post("/api/properties")
async def create_property(request: Request, payload: dict = Depends(verify_token)):
    """Create new property listing."""
    data = await request.json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO properties (agent_id, title, description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payload['user_id'], data['title'], data.get('description'),
        data['property_type'], data['location'], data['price'],
        data.get('bedrooms', 0), data.get('bathrooms', 0),
        data.get('area_sqft', 0), data.get('amenities', ''),
        data.get('status', 'available')
    ))
    
    conn.commit()
    property_id = cursor.lastrowid
    conn.close()
    
    return {"id": property_id, "message": "Property created successfully"}

if __name__ == "__main__":
    # Create demo user on startup
    conn = get_db()
    cursor = conn.cursor()
    
    demo_password = hashlib.sha256('demo123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, email, password_hash, first_name, last_name, phone, experience, areas, property_types, languages, facebook_connected)
        VALUES (1, 'demo@mumbai.com', ?, 'Priya', 'Sharma', '+91 98765 43210', '4-5 years', 
                'Bandra, Andheri, Juhu, Powai', 'Residential, Luxury', 'English, Hindi, Marathi', 0)
    ''', (demo_password,))
    
    # Add demo leads
    demo_leads = [
        (1, 'Rajesh Patel', 'rajesh@email.com', '+91 98765 12345', 'Bandra West', '₹2.5 Cr', '3 BHK Apartment', 'facebook', 'hot', 94, 'Very interested in 3 BHK'),
        (1, 'Kavita Joshi', 'kavita@email.com', '+91 98765 22222', 'Juhu', '₹5.0 Cr', 'Penthouse', 'referral', 'warm', 87, 'Looking for luxury penthouse'),
        (1, 'Vikram Singh', 'vikram@email.com', '+91 98765 11111', 'Powai', '₹3.2 Cr', '4 BHK Villa', 'website', 'contacted', 92, 'Interested in villa with garden'),
        (1, 'Anjali Mehta', 'anjali@email.com', '+91 98765 67890', 'Andheri East', '₹1.8 Cr', '2 BHK Apartment', 'whatsapp', 'new', 79, 'First time buyer'),
        (1, 'Arjun Reddy', 'arjun@email.com', '+91 98765 33333', 'Lower Parel', '₹2.0 Cr', 'Commercial Office', 'facebook', 'warm', 82, 'Business expansion')
    ]
    
    for lead in demo_leads:
        cursor.execute('''
            INSERT OR REPLACE INTO leads (agent_id, name, email, phone, location, budget, property_type, source, status, score, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', lead)
    
    # Add demo properties
    demo_properties = [
        (1, 'Luxury 3 BHK in Bandra West', 'Premium apartment with sea view, modern amenities', 'Residential', 'Bandra West', '₹2.8 Cr', 3, 3, 1250, 'Gym, Pool, Security, Parking', 'available'),
        (1, 'Spacious 4 BHK Villa in Powai', 'Independent villa with garden and parking', 'Residential', 'Powai', '₹3.5 Cr', 4, 4, 2500, 'Garden, Parking, Security', 'available'),
        (1, 'Commercial Office Space Lower Parel', 'Prime location office space for businesses', 'Commercial', 'Lower Parel', '₹1.5 Cr', 0, 2, 800, 'Reception, Parking, AC', 'available')
    ]
    
    for prop in demo_properties:
        cursor.execute('''
            INSERT OR REPLACE INTO properties (agent_id, title, description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', prop)
    
    conn.commit()
    conn.close()
    
    print("🚀 PRODUCTION CRM System Starting...")
    print("📍 Open browser to: http://localhost:8003")
    print("👤 Demo Login: demo@mumbai.com / demo123")
    print("✅ Fully functional with working features!")
    uvicorn.run("production_crm:app", host="0.0.0.0", port=8003, reload=True)
