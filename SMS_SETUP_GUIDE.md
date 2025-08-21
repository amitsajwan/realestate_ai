# SMS Verification Setup Guide

## 🚀 **SMS Service Now Implemented!**

The PropertyAI platform now has full SMS verification functionality for the onboarding process. Here's how to set it up:

## 📱 **SMS Providers Supported**

### 1. **Demo Mode (Default - No Setup Required)**
- Perfect for development and testing
- Shows verification codes in browser console
- No SMS API keys needed
- Automatically active when no provider is configured

### 2. **TextLocal (Recommended for India)**
- **Best for**: Indian market (Pune-Mumbai focus)
- **Cost**: ₹0.10-0.20 per SMS
- **Setup**:
  ```bash
  # Sign up at https://www.textlocal.in/
  # Get API key from dashboard
  SMS_PROVIDER=textlocal
  SMS_API_KEY=your-textlocal-api-key
  SMS_SENDER_ID=PropertyAI
  ```

### 3. **Fast2SMS (Alternative Indian Provider)**
- **Best for**: Budget-conscious Indian deployment
- **Cost**: ₹0.05-0.15 per SMS
- **Setup**:
  ```bash
  # Sign up at https://www.fast2sms.com/
  SMS_PROVIDER=fast2sms
  SMS_API_KEY=your-fast2sms-api-key
  SMS_SENDER_ID=PropertyAI
  ```

### 4. **Twilio (International)**
- **Best for**: Global deployment or premium reliability
- **Cost**: $0.0075-0.01 per SMS
- **Setup**:
  ```bash
  # Sign up at https://www.twilio.com/
  SMS_PROVIDER=twilio
  TWILIO_ACCOUNT_SID=your-account-sid
  TWILIO_AUTH_TOKEN=your-auth-token
  TWILIO_PHONE_NUMBER=your-twilio-number
  ```

## 🔧 **Setup Instructions**

### **Step 1: Choose Your Provider**
For Pune-Mumbai deployment, we recommend **TextLocal**:
- Indian company with good delivery rates
- Supports Hindi/English messages
- Regulatory compliance for Indian market
- Affordable pricing

### **Step 2: Get API Credentials**

#### **TextLocal Setup:**
1. Visit [textlocal.in](https://www.textlocal.in/)
2. Sign up for account
3. Verify your business details
4. Get API key from Dashboard → API Keys
5. Note your Sender ID (usually company name)

#### **Fast2SMS Setup:**
1. Visit [fast2sms.com](https://www.fast2sms.com/)
2. Sign up and verify mobile number
3. Add wallet balance (minimum ₹50)
4. Get API key from Dashboard → Developer API

### **Step 3: Environment Configuration**
Create environment variables (or add to your deployment):

```bash
# For TextLocal
SMS_PROVIDER=textlocal
SMS_API_KEY=your_actual_api_key_here
SMS_SENDER_ID=PropertyAI

# Or for Fast2SMS
SMS_PROVIDER=fast2sms
SMS_API_KEY=your_fast2sms_key_here
```

### **Step 4: Test the Integration**
```bash
# Start the server
python simple_backend.py

# Test SMS endpoint
curl -X POST http://localhost:8003/api/sms/send-verification \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "user_id": "test_user"}'
```

## 🎯 **How It Works**

### **User Experience:**
1. User completes onboarding steps 1-6
2. On Step 7, clicks "Send Verification Code"
3. Receives SMS with 6-digit code
4. Enters code in UI (auto-advances when complete)
5. System verifies code and completes registration

### **Security Features:**
- ✅ **Code Expiration**: 5-minute timeout
- ✅ **Attempt Limiting**: Max 3 verification attempts
- ✅ **Phone Validation**: Indian number format validation
- ✅ **Rate Limiting**: 30-second cooldown between sends
- ✅ **User Isolation**: Codes tied to specific user sessions

### **Backend API:**
```javascript
// Send verification code
POST /api/sms/send-verification
{
  "phone_number": "9876543210",
  "user_id": "user@example.com"
}

// Verify code
POST /api/sms/verify-code
{
  "phone_number": "9876543210", 
  "code": "123456",
  "user_id": "user@example.com"
}
```

## 💰 **Cost Estimates**

### **Expected Volume (Monthly):**
- New agent registrations: 100-500/month
- Verification success rate: 95%
- SMS cost per verification: 1 SMS

### **Monthly SMS Costs:**
- **TextLocal**: ₹50-250/month (100-500 agents)
- **Fast2SMS**: ₹25-125/month (100-500 agents)  
- **Twilio**: ₹60-300/month (100-500 agents)

### **Annual Cost Comparison:**
| Provider | 1,000 agents/year | 5,000 agents/year |
|----------|------------------|-------------------|
| TextLocal | ₹600 | ₹3,000 |
| Fast2SMS | ₹300 | ₹1,500 |
| Twilio | ₹720 | ₹3,600 |

## 🚀 **Production Deployment**

### **Recommended Setup for Pune-Mumbai Launch:**
```bash
# Production environment variables
SMS_PROVIDER=textlocal
SMS_API_KEY=your_production_textlocal_key
SMS_SENDER_ID=PropertyAI
SMS_RATE_LIMIT=60  # seconds between resends
SMS_MAX_ATTEMPTS=3
```

### **Monitoring & Analytics:**
- Track SMS delivery rates
- Monitor verification success rates
- Alert on high failure rates
- Log costs for billing tracking

## 🔧 **Advanced Configuration**

### **Custom Message Templates:**
The SMS service supports customizable message templates:

```python
# English message
"Your PropertyAI verification code is: {code}. Valid for 5 minutes. Do not share this code."

# Hindi message (for Marathi/Hindi speakers)
"आपका PropertyAI सत्यापन कोड है: {code}। 5 मिनट के लिए वैध। यह कोड साझा न करें।"
```

### **Regional Compliance:**
- **TRAI Compliance**: All providers follow Indian telecom regulations
- **DND Registry**: Transactional SMS exempt from DND
- **Sender ID Registration**: Required for branded SMS
- **Message Content**: Pre-approved templates for faster delivery

## ⚠️ **Important Notes**

### **For Development:**
- Use `SMS_PROVIDER=demo` for local testing
- Verification codes shown in browser console
- No real SMS sent or charges incurred

### **For Production:**
- Always use encrypted environment variables
- Monitor SMS delivery rates and failures
- Have backup provider configured
- Test with real phone numbers before launch

### **Legal Requirements:**
- Store SMS logs for compliance
- Respect user opt-out requests
- Follow GDPR/privacy laws for data retention
- Obtain user consent for SMS communications

## 📞 **Support & Troubleshooting**

### **Common Issues:**

1. **"SMS not delivered"**
   - Check phone number format (+91XXXXXXXXXX)
   - Verify API key is active
   - Check provider account balance

2. **"Invalid API key"**
   - Confirm environment variables set correctly
   - Regenerate API key if needed
   - Check provider dashboard for key status

3. **"Rate limit exceeded"**
   - Default 30-second cooldown between sends
   - Increase `SMS_RATE_LIMIT` if needed
   - Monitor for abuse patterns

### **Provider Support:**
- **TextLocal**: support@textlocal.in
- **Fast2SMS**: support@fast2sms.com  
- **Twilio**: support.twilio.com

## 🎯 **Next Steps**

1. **Choose Provider**: Recommend TextLocal for Pune-Mumbai launch
2. **Get API Keys**: Sign up and obtain credentials
3. **Configure Environment**: Set SMS_PROVIDER and API keys
4. **Test Integration**: Verify SMS delivery with real numbers
5. **Monitor Performance**: Track delivery rates and user completion

The SMS verification system is now ready for production deployment in the Pune-Mumbai market!
