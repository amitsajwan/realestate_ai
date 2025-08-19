import axios from 'axios';
import Constants from 'expo-constants';

const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';

class GroqService {
  constructor() {
    this.apiKey = Constants.expoConfig?.extra?.GROQ_API_KEY || process.env.GROQ_API_KEY;
    this.client = axios.create({
      baseURL: GROQ_API_URL,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  async generateResponse(messages, options = {}) {
    try {
      const {
        model = 'llama3-8b-8192',
        temperature = 0.7,
        maxTokens = 1024,
        systemPrompt = this.getDefaultSystemPrompt(),
      } = options;

      const payload = {
        model,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages,
        ],
        temperature,
        max_tokens: maxTokens,
        stream: false,
      };

      const response = await this.client.post('', payload);
      return response.data.choices[0].message.content;
    } catch (error) {
      console.error('GROQ API Error:', error);
      throw new Error(this.handleError(error));
    }
  }

  getDefaultSystemPrompt() {
    return `You are an expert AI assistant for real estate professionals. You help agents with:

1. Property descriptions and marketing content
2. Market analysis and pricing strategies
3. Client communication and follow-up
4. Lead qualification and management
5. Contract insights and negotiations
6. Industry trends and best practices

Always provide practical, actionable advice. Be professional but approachable. Format responses clearly with bullet points or numbered lists when appropriate. Keep responses concise but comprehensive.

When asked about property descriptions, include:
- Key features and amenities
- Location benefits
- Target buyer appeal
- Compelling language that drives interest

For market analysis, consider:
- Recent comparable sales
- Market trends and conditions
- Pricing strategies
- Timing recommendations

For client communications:
- Professional yet personable tone
- Clear next steps
- Value proposition
- Urgency when appropriate`;
  }

  async generatePropertyDescription(propertyData) {
    const prompt = `Generate a compelling property description for the following property:

Property Details:
- Type: ${propertyData.type || 'Not specified'}
- Bedrooms: ${propertyData.bedrooms || 'Not specified'}
- Bathrooms: ${propertyData.bathrooms || 'Not specified'}
- Square Footage: ${propertyData.sqft || 'Not specified'}
- Location: ${propertyData.location || 'Not specified'}
- Key Features: ${propertyData.features?.join(', ') || 'Not specified'}
- Price: ${propertyData.price || 'Not specified'}

Create a professional, engaging description that highlights the property's best features and appeals to potential buyers.`;

    return await this.generateResponse([
      { role: 'user', content: prompt }
    ], {
      systemPrompt: `You are a professional real estate copywriter. Create compelling property descriptions that:
- Highlight unique selling points
- Use descriptive, appealing language
- Include location benefits
- Appeal to the target buyer demographic
- Are 150-250 words long
- Follow real estate marketing best practices`
    });
  }

  async generateMarketAnalysis(location, propertyType) {
    const prompt = `Provide a market analysis for ${propertyType} properties in ${location}. Include:

1. Current market conditions
2. Price trends (last 6-12 months)
3. Inventory levels
4. Average days on market
5. Key factors affecting the market
6. Recommendations for buyers/sellers

Format as a professional market report.`;

    return await this.generateResponse([
      { role: 'user', content: prompt }
    ], {
      systemPrompt: `You are a real estate market analyst. Provide data-driven insights and professional market analysis. Use industry terminology appropriately and structure information clearly.`
    });
  }

  async generateClientFollowUp(clientInfo, context) {
    const prompt = `Generate a follow-up email for a real estate client:

Client Information:
- Name: ${clientInfo.name}
- Interest: ${clientInfo.interest}
- Last Contact: ${clientInfo.lastContact}
- Stage: ${clientInfo.stage}

Context: ${context}

Create a professional, personalized follow-up email that moves the relationship forward.`;

    return await this.generateResponse([
      { role: 'user', content: prompt }
    ], {
      systemPrompt: `You are a real estate professional writing client follow-up communications. Create emails that are:
- Professional but warm and personal
- Include clear next steps
- Provide value to the client
- Maintain appropriate urgency
- Are concise but comprehensive`
    });
  }

  async generatePriceRecommendation(propertyData, marketData) {
    const prompt = `Provide pricing recommendations for this property:

Property Details:
${JSON.stringify(propertyData, null, 2)}

Market Context:
${marketData}

Provide:
1. Suggested listing price range
2. Reasoning behind the recommendation
3. Market positioning strategy
4. Potential pricing adjustments based on market response`;

    return await this.generateResponse([
      { role: 'user', content: prompt }
    ], {
      systemPrompt: `You are a real estate pricing strategist. Provide data-driven pricing recommendations with clear reasoning. Consider market conditions, property features, and competitive positioning.`
    });
  }

  async qualifyLead(leadData) {
    const prompt = `Analyze this lead and provide qualification insights:

Lead Information:
- Source: ${leadData.source}
- Budget: ${leadData.budget}
- Timeline: ${leadData.timeline}
- Requirements: ${leadData.requirements}
- Contact Method: ${leadData.contactMethod}
- Initial Inquiry: ${leadData.inquiry}

Provide:
1. Lead score (1-10)
2. Qualification assessment
3. Recommended next steps
4. Potential concerns or red flags
5. Best approach for follow-up`;

    return await this.generateResponse([
      { role: 'user', content: prompt }
    ], {
      systemPrompt: `You are a real estate lead qualification expert. Assess leads based on budget, timeline, motivation, and fit. Provide actionable recommendations for agent follow-up.`
    });
  }

  handleError(error) {
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.error?.message || 'Unknown API error';
      
      switch (status) {
        case 401:
          return 'Invalid API key. Please check your GROQ API configuration.';
        case 429:
          return 'Rate limit exceeded. Please try again later.';
        case 500:
          return 'GROQ service temporarily unavailable. Please try again.';
        default:
          return `API Error: ${message}`;
      }
    } else if (error.request) {
      return 'Network error. Please check your internet connection.';
    } else {
      return 'An unexpected error occurred. Please try again.';
    }
  }
}

export default new GroqService();