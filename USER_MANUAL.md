# Real Estate CRM – User Manual

This guide helps agents use the Production CRM at http://localhost:8004.

## Demo Login
- Email: demo@mumbai.com
- Password: demo123

## 1) Sign In
1. Open http://localhost:8004
2. Enter email and password
3. Click "Login to Dashboard"

If you’re logged out, you’ll be redirected back to login.

## 2) Dashboard Overview
- Stats cards: Total Leads, Hot Leads, Properties
- Quick Actions: Add Lead, Add Property
- Recent Leads & Properties tables

Switch sections via the top navigation:
- Dashboard, Leads, Properties, Settings

## 3) Leads
- Add Lead: Click "Add Lead" to open the modal
  - Fill name, phone, optional email/location/budget/type
  - Save to create the lead
- View Leads: Recent leads show on Dashboard; full list on Leads tab
- Actions:
  - Call: Simulated phone action
  - WhatsApp: Opens wa.me with pre-filled message

## 4) Properties
- Add Property: Click "Add Property" to open the modal
  - Fill title, type, location, price, optional details
- View Properties: Table with key fields
- Share: Click 📤 to simulate sharing (Facebook mock flow)

## 5) Settings
- Profile: Email, phone, experience, areas, languages
- Facebook: Connect/select page (mock endpoints)
- WhatsApp: Placeholder for Business API integration

## 6) Logging Out
- Click Logout in the header
- Token is removed; you’ll return to login

## FAQs
- I can’t see data?
  - Ensure you logged in first; token must be present
  - Refresh Dashboard; data loads from /api/leads and /api/properties
- Can this persist data?
  - Yes. In Docker setup, MongoDB persists via docker volume
- Mobile support?
  - The UI is responsive; works on phones and tablets

## Troubleshooting
- Server not reachable?
  - Ensure Docker is running: `docker compose -f docker-compose.crm.yml up -d`
  - Check http://localhost:8004
- Login fails?
  - Use demo credentials above
  - Clear browser localStorage and retry
- API error 401
  - Re-login to refresh token

## Getting Help
- Report issues to the engineering team with steps and screenshots
- Provide browser console output (F12) and /api responses if possible
