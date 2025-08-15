"""AI Lead Scoring Service for CRM system."""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio

from groq import AsyncGroq
from models.crm import Lead, LeadScore, LeadInteraction, InteractionType
from repositories.crm_repository import CRMRepository


class LeadScoringService:
    """AI-powered lead scoring using LLM analysis."""
    
    def __init__(self, groq_client: AsyncGroq, crm_repo: CRMRepository):
        self.groq_client = groq_client
        self.crm_repo = crm_repo
        
    async def score_lead(self, lead: Lead) -> LeadScore:
        """Generate AI-powered lead score."""
        try:
            # Get lead interactions for context
            interactions = await self.crm_repo.get_lead_interactions(lead.id, limit=10)
            
            # Analyze different scoring factors
            content_score = await self._analyze_content(lead, interactions)
            engagement_score = await self._calculate_engagement_score(lead, interactions)
            timing_score = self._calculate_timing_score(lead, interactions)
            source_score = self._calculate_source_score(lead)
            profile_score = await self._analyze_profile(lead)
            
            # Calculate weighted final score
            weighted_score = (
                content_score['score'] * 0.30 +
                engagement_score['score'] * 0.25 +
                timing_score['score'] * 0.20 +
                source_score['score'] * 0.15 +
                profile_score['score'] * 0.10
            )
            
            # Calculate confidence based on available data
            confidence = self._calculate_confidence(lead, interactions)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                lead, content_score, engagement_score, timing_score
            )
            
            return LeadScore(
                score=int(min(100, max(0, weighted_score))),
                confidence=confidence,
                factors={
                    'content_analysis': content_score,
                    'engagement_score': engagement_score,
                    'timing_analysis': timing_score,
                    'source_quality': source_score,
                    'profile_analysis': profile_score
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            # Fallback scoring if AI fails
            return self._fallback_scoring(lead, interactions if 'interactions' in locals() else [])
    
    async def _analyze_content(self, lead: Lead, interactions: List[LeadInteraction]) -> Dict[str, Any]:
        """Analyze message content using LLM."""
        try:
            # Prepare content for analysis
            all_messages = []
            if lead.initial_message:
                all_messages.append(f"Initial: {lead.initial_message}")
            
            for interaction in interactions[:5]:  # Last 5 interactions
                if interaction.message:
                    direction = "Agent" if interaction.direction.value == "outbound" else "Customer"
                    all_messages.append(f"{direction}: {interaction.message}")
            
            content_text = "\n".join(all_messages)
            
            if not content_text.strip():
                return {
                    'score': 50,
                    'urgency': 'unknown',
                    'intent_clarity': 'low',
                    'budget_indicators': 'none',
                    'explanation': 'No message content to analyze'
                }
            
            prompt = f"""
            Analyze this real estate lead conversation for scoring factors:
            
            Conversation:
            {content_text}
            
            Rate these factors on a scale of 1-10:
            1. Urgency level (immediate need vs casual browsing)
            2. Intent clarity (specific requirements vs vague interest)
            3. Budget indicators (mentions price range, financing, affordability)
            4. Seriousness (detailed questions vs generic inquiries)
            5. Decision authority (mentions family, spouse, decision process)
            
            Property Interest Analysis:
            - What type of property are they looking for?
            - What's their budget range if mentioned?
            - How urgent is their need?
            - Are they ready to make decisions?
            
            Return JSON format:
            {{
                "urgency_score": 1-10,
                "intent_score": 1-10,
                "budget_score": 1-10,
                "seriousness_score": 1-10,
                "authority_score": 1-10,
                "overall_content_score": 1-10,
                "urgency_level": "immediate|within_month|within_3_months|flexible",
                "intent_clarity": "high|medium|low",
                "budget_indicators": "strong|weak|none",
                "key_insights": ["insight1", "insight2"],
                "explanation": "Brief explanation of scoring"
            }}
            """
            
            response = await self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse LLM response
            content_analysis = json.loads(response.choices[0].message.content)
            
            # Convert to 0-100 scale
            score = content_analysis.get('overall_content_score', 5) * 10
            
            return {
                'score': score,
                'urgency': content_analysis.get('urgency_level', 'unknown'),
                'intent_clarity': content_analysis.get('intent_clarity', 'medium'),
                'budget_indicators': content_analysis.get('budget_indicators', 'none'),
                'key_insights': content_analysis.get('key_insights', []),
                'explanation': content_analysis.get('explanation', 'AI content analysis'),
                'detailed_scores': {
                    'urgency': content_analysis.get('urgency_score', 5),
                    'intent': content_analysis.get('intent_score', 5),
                    'budget': content_analysis.get('budget_score', 5),
                    'seriousness': content_analysis.get('seriousness_score', 5),
                    'authority': content_analysis.get('authority_score', 5)
                }
            }
            
        except Exception as e:
            # Fallback to keyword-based analysis
            return self._keyword_based_content_analysis(lead, interactions)
    
    def _keyword_based_content_analysis(self, lead: Lead, interactions: List[LeadInteraction]) -> Dict[str, Any]:
        """Fallback content analysis using keywords."""
        content = lead.initial_message or ""
        for interaction in interactions:
            if interaction.message:
                content += " " + interaction.message
        
        content_lower = content.lower()
        
        # Urgency keywords
        urgency_keywords = ['urgent', 'immediate', 'asap', 'quickly', 'soon', 'this week', 'this month']
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in content_lower) * 20
        
        # Intent keywords
        intent_keywords = ['buy', 'purchase', 'looking for', 'need', 'want', 'budget', 'price', 'cost']
        intent_score = min(100, sum(1 for keyword in intent_keywords if keyword in content_lower) * 15)
        
        # Budget keywords
        budget_keywords = ['budget', 'price', 'cost', 'affordable', 'lakhs', 'crores', 'loan', 'emi']
        budget_score = min(100, sum(1 for keyword in budget_keywords if keyword in content_lower) * 25)
        
        # Calculate overall score
        overall_score = (urgency_score + intent_score + budget_score) / 3
        
        return {
            'score': min(100, overall_score),
            'urgency': 'high' if urgency_score > 40 else 'medium' if urgency_score > 20 else 'low',
            'intent_clarity': 'high' if intent_score > 60 else 'medium' if intent_score > 30 else 'low',
            'budget_indicators': 'strong' if budget_score > 50 else 'weak' if budget_score > 25 else 'none',
            'explanation': 'Keyword-based content analysis (fallback)'
        }
    
    async def _calculate_engagement_score(self, lead: Lead, interactions: List[LeadInteraction]) -> Dict[str, Any]:
        """Calculate engagement score based on interaction patterns."""
        if not interactions:
            return {
                'score': 30,
                'interaction_count': 0,
                'response_rate': 0.0,
                'avg_response_time': 0,
                'explanation': 'No interactions to analyze'
            }
        
        # Count different types of interactions
        total_interactions = len(interactions)
        inbound_interactions = len([i for i in interactions if i.direction.value == "inbound"])
        outbound_interactions = len([i for i in interactions if i.direction.value == "outbound"])
        
        # Calculate response rate (inbound / outbound ratio)
        response_rate = inbound_interactions / outbound_interactions if outbound_interactions > 0 else 0
        
        # Analyze response times
        response_times = []
        for i, interaction in enumerate(interactions[1:], 1):
            prev_interaction = interactions[i-1]
            if (prev_interaction.direction.value == "outbound" and 
                interaction.direction.value == "inbound"):
                time_diff = (interaction.created_at - prev_interaction.created_at).total_seconds() / 3600
                response_times.append(time_diff)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 24
        
        # Score based on engagement factors
        interaction_score = min(100, total_interactions * 15)  # More interactions = higher score
        response_rate_score = min(100, response_rate * 100)    # Higher response rate = higher score
        response_time_score = max(0, 100 - (avg_response_time * 2))  # Faster response = higher score
        
        overall_score = (interaction_score + response_rate_score + response_time_score) / 3
        
        return {
            'score': overall_score,
            'interaction_count': total_interactions,
            'response_rate': response_rate,
            'avg_response_time': avg_response_time,
            'engagement_level': 'high' if overall_score > 70 else 'medium' if overall_score > 40 else 'low',
            'explanation': f'Based on {total_interactions} interactions with {response_rate:.1%} response rate'
        }
    
    def _calculate_timing_score(self, lead: Lead, interactions: List[LeadInteraction]) -> Dict[str, Any]:
        """Calculate score based on timing patterns."""
        now = datetime.utcnow()
        lead_age = (now - lead.created_at).total_seconds() / 3600  # hours
        
        # Fresh leads score higher
        freshness_score = max(0, 100 - (lead_age * 2))  # Decreases by 2 points per hour
        
        # Business hours analysis
        business_hour_interactions = 0
        for interaction in interactions:
            hour = interaction.created_at.hour
            if 9 <= hour <= 18:  # 9 AM to 6 PM
                business_hour_interactions += 1
        
        business_hour_ratio = (business_hour_interactions / len(interactions)) if interactions else 0
        business_hour_score = business_hour_ratio * 100
        
        # Last contact recency
        last_contact_score = 50  # Default
        if lead.last_contact:
            hours_since_contact = (now - lead.last_contact).total_seconds() / 3600
            last_contact_score = max(0, 100 - (hours_since_contact * 3))
        
        overall_score = (freshness_score + business_hour_score + last_contact_score) / 3
        
        return {
            'score': overall_score,
            'lead_age_hours': lead_age,
            'business_hour_ratio': business_hour_ratio,
            'hours_since_last_contact': (now - lead.last_contact).total_seconds() / 3600 if lead.last_contact else None,
            'explanation': f'Lead is {lead_age:.1f} hours old with {business_hour_ratio:.1%} business hour activity'
        }
    
    def _calculate_source_score(self, lead: Lead) -> Dict[str, Any]:
        """Calculate score based on lead source quality."""
        source_scores = {
            'website': 90,
            'referral': 85,
            'phone_call': 80,
            'facebook_message': 75,
            'whatsapp': 70,
            'email': 65,
            'facebook_comment': 60,
            'walk_in': 50
        }
        
        score = source_scores.get(lead.source.value, 50)
        
        return {
            'score': score,
            'source': lead.source.value,
            'quality_level': 'high' if score > 75 else 'medium' if score > 60 else 'low',
            'explanation': f'Source quality: {lead.source.value} typically converts at {score}% rate'
        }
    
    async def _analyze_profile(self, lead: Lead) -> Dict[str, Any]:
        """Analyze lead profile information."""
        score = 50  # Base score
        
        # Score based on available contact information
        if lead.phone:
            score += 20
        if lead.email:
            score += 15
        if lead.whatsapp_number:
            score += 10
        if lead.facebook_id:
            score += 5
        
        # Score based on property interest completeness
        if lead.property_interest:
            pi = lead.property_interest
            if pi.budget_min or pi.budget_max:
                score += 15
            if pi.location:
                score += 10
            if pi.property_type:
                score += 10
            if pi.urgency:
                urgency_scores = {'immediate': 20, 'within_month': 15, 'within_3_months': 10, 'flexible': 5}
                score += urgency_scores.get(pi.urgency, 0)
        
        return {
            'score': min(100, score),
            'contact_completeness': self._calculate_contact_completeness(lead),
            'property_interest_score': self._calculate_property_interest_score(lead),
            'explanation': 'Profile analysis based on available information completeness'
        }
    
    def _calculate_contact_completeness(self, lead: Lead) -> float:
        """Calculate how complete the contact information is."""
        total_fields = 4
        filled_fields = sum([
            bool(lead.phone),
            bool(lead.email),
            bool(lead.whatsapp_number),
            bool(lead.facebook_id)
        ])
        return filled_fields / total_fields
    
    def _calculate_property_interest_score(self, lead: Lead) -> float:
        """Calculate how detailed the property interest is."""
        if not lead.property_interest:
            return 0.0
        
        pi = lead.property_interest
        total_fields = 7
        filled_fields = sum([
            bool(pi.property_type),
            bool(pi.budget_min or pi.budget_max),
            bool(pi.location),
            bool(pi.bedrooms),
            bool(pi.preferred_area),
            bool(pi.urgency),
            bool(pi.purpose)
        ])
        return filled_fields / total_fields
    
    def _calculate_confidence(self, lead: Lead, interactions: List[LeadInteraction]) -> float:
        """Calculate confidence level in the scoring."""
        confidence_factors = []
        
        # Message content availability
        if lead.initial_message and len(lead.initial_message) > 20:
            confidence_factors.append(0.3)
        elif lead.initial_message:
            confidence_factors.append(0.15)
        else:
            confidence_factors.append(0.0)
        
        # Interaction history
        if len(interactions) >= 3:
            confidence_factors.append(0.25)
        elif len(interactions) >= 1:
            confidence_factors.append(0.15)
        else:
            confidence_factors.append(0.05)
        
        # Contact information completeness
        confidence_factors.append(self._calculate_contact_completeness(lead) * 0.2)
        
        # Property interest completeness
        confidence_factors.append(self._calculate_property_interest_score(lead) * 0.15)
        
        # Time factor (more time = more data = higher confidence)
        lead_age_hours = (datetime.utcnow() - lead.created_at).total_seconds() / 3600
        time_confidence = min(0.1, lead_age_hours / 24 * 0.1)  # Max 0.1 after 24 hours
        confidence_factors.append(time_confidence)
        
        return min(1.0, sum(confidence_factors))
    
    def _generate_recommendations(
        self,
        lead: Lead,
        content_score: Dict[str, Any],
        engagement_score: Dict[str, Any],
        timing_score: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for the agent."""
        recommendations = []
        
        # Based on content analysis
        if content_score['urgency'] == 'high':
            recommendations.append("🔥 High urgency lead - prioritize immediate contact")
        elif content_score['urgency'] == 'low':
            recommendations.append("📅 Schedule follow-up sequence for gradual nurturing")
        
        if content_score['budget_indicators'] == 'strong':
            recommendations.append("💰 Budget mentioned - prepare property options in their range")
        elif content_score['budget_indicators'] == 'none':
            recommendations.append("❓ Ask about budget range to qualify better")
        
        # Based on engagement
        if engagement_score['response_rate'] > 0.7:
            recommendations.append("📱 Highly engaged - suggest property viewing or call")
        elif engagement_score['response_rate'] < 0.3:
            recommendations.append("📧 Low engagement - try different communication channel")
        
        if engagement_score['avg_response_time'] < 1:  # Less than 1 hour
            recommendations.append("⚡ Quick responder - maintain momentum with immediate follow-up")
        
        # Based on timing
        if timing_score['lead_age_hours'] < 2:
            recommendations.append("🆕 Fresh lead - contact within next hour for best results")
        elif timing_score['lead_age_hours'] > 24:
            recommendations.append("⏰ Older lead - use re-engagement strategy")
        
        # Based on profile completeness
        contact_completeness = self._calculate_contact_completeness(lead)
        if contact_completeness < 0.5:
            recommendations.append("📋 Collect more contact details for better follow-up")
        
        if not lead.property_interest or self._calculate_property_interest_score(lead) < 0.5:
            recommendations.append("🏠 Gather more property requirements details")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations = [
                "📞 Follow up with personalized message",
                "🏠 Share relevant property options",
                "📅 Schedule property viewing if interested"
            ]
        
        return recommendations[:4]  # Limit to top 4 recommendations
    
    def _fallback_scoring(self, lead: Lead, interactions: List[LeadInteraction]) -> LeadScore:
        """Fallback scoring when AI analysis fails."""
        base_score = 50
        
        # Simple scoring based on available data
        if lead.initial_message and len(lead.initial_message) > 50:
            base_score += 15
        
        if len(interactions) > 2:
            base_score += 10
        
        if lead.phone and lead.email:
            base_score += 10
        
        if lead.property_interest and lead.property_interest.budget_min:
            base_score += 15
        
        # Source-based adjustment
        source_adjustments = {
            'website': 10, 'referral': 10, 'phone_call': 5,
            'facebook_comment': -5, 'walk_in': -10
        }
        base_score += source_adjustments.get(lead.source.value, 0)
        
        return LeadScore(
            score=min(100, max(0, base_score)),
            confidence=0.5,
            factors={'fallback': True},
            recommendations=["Contact lead to gather more information", "Follow up within 24 hours"]
        )
