# Real Estate AI CRM - User Manual

## 🎯 Quick Start Guide

### 🔑 Demo Login Credentials
- **Email**: demo@mumbai.com
- **Password**: demo123

### 🌐 Access Points
- **Production CRM**: http://localhost:8004 (Full features with MongoDB)
- **Development Server**: http://localhost:8003 (Quick testing)

## 📊 Dashboard Overview

### 1. **Login Process**
1. Open http://localhost:8004
2. Enter demo credentials
3. Click "Login to Dashboard"
4. You'll be redirected to the main dashboard

### 2. **Main Dashboard Interface**
The dashboard contains 5 main sections accessible via top navigation:

#### **Dashboard Tab** 
- **Statistics Cards**: Total leads, active properties, recent activity
- **Quick Actions**: Add new lead, create property listing
- **Recent Activity**: Latest leads and property updates
- **Facebook Integration Panel**: Connection status and posting interface

#### **Leads Tab**
- **Lead List**: View all leads with search and filter options  
- **Add New Lead**: Create leads with contact information
- **Lead Details**: Name, phone, email, property interests, status
- **Actions**: Call, WhatsApp, update status, delete

#### **Properties Tab**
- **Property Listings**: View all properties with details
- **Add Property**: Create new property listings
- **Property Details**: Address, price, bedrooms, bathrooms, type
- **Actions**: Edit, share to Facebook, mark as sold

#### **AI Tools Tab**
- **Content Generation**: Create professional real estate posts
- **Templates**: Just Listed, Open House, Price Drop, Sold
- **Multi-language**: Generate content in 7 languages
- **Copy to Facebook**: Transfer generated content to posting area

#### **Settings Tab**
- **Profile Management**: Update agent information
- **Facebook Integration**: Connect/disconnect Facebook pages
- **Account Settings**: Password change, preferences

## 🤖 AI Content Generation

### 1. **Generate Professional Posts**
1. Go to **AI Tools** tab
2. Fill in property details:
   - Property address
   - Price
   - Bedrooms/bathrooms
   - Property type
3. Select template (Just Listed, Open House, etc.)
4. Choose language if needed
5. Click "Generate Post"
6. Review generated content
7. Use "Copy to Facebook" to transfer content

### 2. **Available Templates**
- **Just Listed**: New property announcements
- **Open House**: Event promotions  
- **Price Drop**: Price reduction alerts
- **Sold**: Celebration posts
- **Market Update**: General market news

## 📘 Facebook Integration

### 1. **Connect Facebook Account**
1. Go to **Settings** tab
2. Click "Connect Facebook" in Facebook Integration section
3. Complete OAuth authorization on Facebook
4. Select which Facebook page to use for posting
5. Return to dashboard - status will show "Connected"

### 2. **Post to Facebook**
1. Create content using AI Tools or write manually
2. Go to **Dashboard** tab
3. Use Facebook Integration panel
4. Enter/paste content in message area
5. Click "Post to Page"
6. Confirm success message

### 3. **Manage Multiple Pages**
- If you have multiple Facebook pages
- Use page selection dropdown in Facebook panel
- Switch between pages for different content

## 👥 Lead Management

### 1. **Add New Leads**
1. Go to **Leads** tab
2. Click "Add Lead" button
3. Fill required information:
   - Full name (required)
   - Email address (required)
   - Phone number
   - Property interests
   - Budget range
   - Lead source
4. Click "Save Lead"

### 2. **Manage Existing Leads**
- **View All Leads**: Complete list with status indicators
- **Search Leads**: Find by name, email, or phone
- **Filter by Status**: New, contacted, qualified, closed
- **Update Status**: Track lead progression
- **Contact Actions**: Call, WhatsApp, email integration

### 3. **Lead Status Workflow**
- **New** → **Contacted** → **Qualified** → **Closed**
- Update status based on interaction progress
- Track follow-up dates and next actions

## 🏢 Property Management

### 1. **Add Properties**
1. Go to **Properties** tab
2. Click "Add Property" button  
3. Enter property details:
   - Property title/address
   - Property type (apartment, house, etc.)
   - Location/area
   - Price
   - Bedrooms and bathrooms
   - Description
4. Click "Save Property"

### 2. **Property Actions**
- **View Details**: Complete property information
- **Edit Property**: Update details and status
- **Share to Facebook**: Generate social media posts
- **Mark as Sold**: Update property status
- **Delete Property**: Remove from listings

## 🔧 Settings & Configuration

### 1. **Profile Management**
- Update agent information
- Contact details and specializations  
- Areas served and property types
- Languages spoken

### 2. **Facebook Settings**
- Connect/disconnect Facebook account
- Select active Facebook page
- View connection status
- Test posting capabilities

### 3. **Account Security**
- Change password (when available)
- View login history
- Manage active sessions

## 🚨 Troubleshooting

### **Common Issues**

#### **Cannot Login**
- Verify demo credentials: demo@mumbai.com / demo123
- Clear browser cache and cookies
- Check if server is running on correct port

#### **Facebook Not Connecting**
- Ensure Facebook app is configured with proper credentials
- Check OAuth redirect URI matches exactly
- Verify Facebook app is in correct mode (development/production)

#### **AI Content Not Generating**
- Verify Groq API key is configured
- Check internet connection
- Try different templates or simpler property details

#### **Data Not Saving**
- Ensure MongoDB is running (for production CRM)
- Check database connection in server logs
- Verify all required fields are filled

### **Getting Help**
1. Check server terminal for error messages
2. Use browser developer tools to check network requests
3. Refer to technical documentation in repository
4. Check API documentation at `/docs` endpoint

## 🎯 Best Practices

### **Lead Management**
- Update lead status promptly after interactions
- Add detailed notes about conversations
- Set follow-up reminders
- Use AI tools to create personalized content

### **Facebook Posting**
- Use AI-generated content for professional posts
- Post regularly to maintain engagement
- Include high-quality property images when available
- Monitor post performance and engagement

### **Property Listings**
- Include complete and accurate details
- Use professional descriptions
- Update status promptly when sold
- Generate multiple content variations for marketing

---

**Need additional help?** Check the technical documentation in the repository or contact system administrator.
