"""
Claude API service for STRATUS Bug Advisor
Handles all interactions with the Claude API
"""

import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

import anthropic
from anthropic import APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)

class ClaudeService:
    """Service class for Claude API interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude service with API key"""
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        else:
            logger.warning("Claude API key not provided")
    
    def is_available(self) -> bool:
        """Check if Claude service is available"""
        return self.client is not None
    
    def get_system_prompt(self, product: str) -> str:
        """Get system prompt for Claude based on product"""
        base_prompt = """You are the STRATUS Bug Advisor AI with access to an isolated STRATUS knowledge base.

CRITICAL: Only reference information from the dedicated STRATUS knowledge base. Never include information from other sources or projects.

Product Context: {product} - Focus on {product}-specific issues and solutions.

Structure your response with exactly these sections:
## Root Cause Analysis
[STRATUS-specific analysis based on historical patterns]

## Immediate Solutions
[Proven STRATUS fixes with step-by-step instructions]

## Files/Areas to Check
[Specific STRATUS components, files, or configuration areas]

## Testing Steps
[STRATUS-specific testing procedures]

## Related Historical Issues
[Reference similar STRATUS tickets and resolutions from the knowledge base]

Focus exclusively on STRATUS products: Allocator, FormsPlus, Premium Tax, Municipal.
Provide technical, actionable guidance based only on the STRATUS knowledge base.
Be specific about file paths, configuration settings, and code changes where applicable.
Include relevant ticket numbers (TTS-XXXX, ClickUp IDs) when referencing historical issues."""

        product_contexts = {
            'allocator': """Focus on TTS ticket patterns, geocoding issues, batch processing problems, and allocation algorithm errors.
Common areas: TaxAllocation.exe, geocoding services, batch processing workflows, match code validation, address standardization.
Key files: allocation.config, geocoding.xml, batch_processor.py, address_validator.cs""",
            
            'formsplus': """Focus on ClickUp tickets, tree structure problems, form rendering issues, and data validation errors.
Common areas: Form tree navigation, dynamic form generation, field validation, user permissions, data persistence.
Key files: form_tree.js, validation_rules.json, form_renderer.tsx, permissions.config""",
            
            'premium_tax': """Focus on calculation errors, e-filing problems, rate table issues, and compliance validation.
Common areas: Tax calculation engine, e-filing integrations, rate table management, compliance checks, reporting.
Key files: tax_calculator.py, efile_processor.cs, rate_tables.sql, compliance_rules.xml""",
            
            'municipal': """Focus on municipal code issues, rate calculation problems, jurisdiction mapping, and data import errors.
Common areas: Municipal code management, jurisdiction boundaries, rate calculations, data imports, mapping services.
Key files: municipal_codes.db, jurisdiction_mapper.py, rate_engine.cs, import_processor.java"""
        }
        
        context = product_contexts.get(product.lower(), 'General STRATUS system issues and solutions.')
        return base_prompt.format(product=product.title()) + f"\n\nSpecific Focus: {context}"
    
    def analyze_bug(self, query: str, product: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Analyze bug query using Claude API
        
        Returns:
            Tuple of (response_text, error_message, confidence_score)
        """
        if not self.client:
            return None, "Claude API client not initialized", 0.0
        
        try:
            system_prompt = self.get_system_prompt(product)
            
            # Prepare the message
            message_content = f"""Bug Report for {product.title()}:

{query}

Please analyze this issue and provide a structured response following the required format."""
            
            # Call Claude API
            start_time = datetime.now()
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2500,
                temperature=0.1,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": message_content
                }]
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Claude API response received in {response_time:.2f}s")
            
            if not message.content:
                return None, "Empty response from Claude API", 0.0
            
            response_text = message.content[0].text
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(response_text, query, product)
            
            return response_text, None, confidence
            
        except RateLimitError as e:
            logger.warning(f"Claude API rate limit exceeded: {e}")
            return None, "Rate limit exceeded. Please try again later.", 0.0
            
        except APIConnectionError as e:
            logger.error(f"Claude API connection error: {e}")
            return None, "Connection error. Please check your internet connection.", 0.0
            
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            return None, f"API error: {str(e)}", 0.0
            
        except Exception as e:
            logger.error(f"Unexpected error in Claude analysis: {e}")
            return None, f"Unexpected error: {str(e)}", 0.0
    
    def _calculate_confidence(self, response: str, query: str, product: str) -> float:
        """Calculate confidence score based on response quality"""
        try:
            confidence = 0.5  # Base confidence
            
            # Check for required sections
            required_sections = [
                "Root Cause Analysis",
                "Immediate Solutions", 
                "Files/Areas to Check",
                "Testing Steps",
                "Related Historical Issues"
            ]
            
            sections_found = sum(1 for section in required_sections if section in response)
            confidence += (sections_found / len(required_sections)) * 0.3
            
            # Check for specific technical details
            technical_indicators = [
                ".exe", ".config", ".xml", ".py", ".cs", ".js", ".tsx", ".json", ".sql",
                "TTS-", "ClickUp", "batch", "geocoding", "allocation", "validation",
                "file", "directory", "database", "API", "service", "configuration"
            ]
            
            technical_found = sum(1 for indicator in technical_indicators if indicator.lower() in response.lower())
            confidence += min(technical_found / 10, 0.2)  # Max 0.2 boost
            
            # Check response length (longer responses tend to be more detailed)
            if len(response) > 1000:
                confidence += 0.1
            elif len(response) > 500:
                confidence += 0.05
            
            # Product-specific keywords
            product_keywords = {
                'allocator': ['geocoding', 'allocation', 'TTS-', 'match code', 'address'],
                'formsplus': ['form', 'tree', 'ClickUp', 'validation', 'field'],
                'premium_tax': ['tax', 'calculation', 'e-filing', 'rate', 'compliance'],
                'municipal': ['municipal', 'jurisdiction', 'code', 'boundary', 'mapping']
            }
            
            if product.lower() in product_keywords:
                keywords_found = sum(1 for keyword in product_keywords[product.lower()] 
                                   if keyword.lower() in response.lower())
                confidence += min(keywords_found / 5, 0.1)  # Max 0.1 boost
            
            # Ensure confidence is within valid range
            return min(max(confidence, 0.1), 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.7  # Default confidence if calculation fails
    
    def test_connection(self) -> Dict[str, any]:
        """Test Claude API connection"""
        if not self.client:
            return {
                'available': False,
                'error': 'Client not initialized',
                'response_time': None
            }
        
        try:
            start_time = datetime.now()
            
            # Simple test message
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=50,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": "Hello, please respond with 'API connection successful'"
                }]
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if message.content and "successful" in message.content[0].text.lower():
                return {
                    'available': True,
                    'error': None,
                    'response_time': response_time
                }
            else:
                return {
                    'available': False,
                    'error': 'Unexpected response format',
                    'response_time': response_time
                }
                
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'response_time': None
            }
    
    def get_fallback_response(self, product: str) -> str:
        """Get fallback response when Claude API is unavailable"""
        fallback_responses = {
            'allocator': """## Service Temporarily Unavailable

The STRATUS Bug Advisor AI service is currently unavailable. Please try the following general troubleshooting steps for Allocator issues:

## Common Allocator Issues
- Check TaxAllocation.exe configuration files
- Verify geocoding service connectivity
- Review batch processing logs
- Validate input data format

## Files to Check
- allocation.config
- geocoding.xml
- batch_processor.py
- Error logs in /logs/allocator/

Please try again in a few minutes or contact support if the issue persists.""",

            'formsplus': """## Service Temporarily Unavailable

The STRATUS Bug Advisor AI service is currently unavailable. Please try the following general troubleshooting steps for FormsPlus issues:

## Common FormsPlus Issues
- Check form tree navigation
- Verify field validation rules
- Review user permissions
- Check database connections

## Files to Check
- form_tree.js
- validation_rules.json
- form_renderer.tsx
- permissions.config

Please try again in a few minutes or contact support if the issue persists.""",

            'premium_tax': """## Service Temporarily Unavailable

The STRATUS Bug Advisor AI service is currently unavailable. Please try the following general troubleshooting steps for Premium Tax issues:

## Common Premium Tax Issues
- Check tax calculation engine
- Verify e-filing configurations
- Review rate table updates
- Validate compliance rules

## Files to Check
- tax_calculator.py
- efile_processor.cs
- rate_tables.sql
- compliance_rules.xml

Please try again in a few minutes or contact support if the issue persists.""",

            'municipal': """## Service Temporarily Unavailable

The STRATUS Bug Advisor AI service is currently unavailable. Please try the following general troubleshooting steps for Municipal issues:

## Common Municipal Issues
- Check municipal code database
- Verify jurisdiction mappings
- Review rate calculations
- Check data import processes

## Files to Check
- municipal_codes.db
- jurisdiction_mapper.py
- rate_engine.cs
- import_processor.java

Please try again in a few minutes or contact support if the issue persists."""
        }
        
        return fallback_responses.get(product.lower(), 
            "## Service Temporarily Unavailable\n\nThe STRATUS Bug Advisor AI service is currently unavailable. Please try again in a few minutes or contact support.")

# Global instance
claude_service = ClaudeService()
