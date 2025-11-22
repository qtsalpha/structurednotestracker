"""
AI-Powered Termsheet Extraction
Uses Claude API to extract structured note data from PDF termsheets
"""

import PyPDF2
from typing import Dict, Optional
import json
import os


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file
    
    Args:
        pdf_file: Streamlit uploaded file object
    
    Returns:
        Extracted text from PDF
    """
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        # Read first 8 pages (usually sufficient for termsheets)
        for page in reader.pages[:8]:
            text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def extract_note_data_with_claude(pdf_text: str, api_key: str) -> Optional[Dict]:
    """
    Use Claude API to extract structured note data from termsheet text
    
    Args:
        pdf_text: Text extracted from PDF
        api_key: Claude API key
    
    Returns:
        Dictionary with extracted note data
    """
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""You are a financial analyst extracting data from a structured note termsheet. 

Extract the following information and return ONLY a JSON object with these exact fields:

{{
  "customer_name": "Client name if mentioned, otherwise 'Unknown'",
  "type_of_structured_product": "FCN or Phoenix or BEN",
  "notional_amount": amount as number,
  "isin": "ISIN code",
  "trade_date": "YYYY-MM-DD",
  "issue_date": "YYYY-MM-DD",
  "observation_start_date": "YYYY-MM-DD or trade_date",
  "final_valuation_date": "YYYY-MM-DD",
  "coupon_payment_dates": "comma-separated dates in YYYY-MM-DD format",
  "coupon_per_annum": decimal (e.g., 0.13 for 13%),
  "coupon_barrier": price if Phoenix/BEN, null if FCN,
  "ko_type": "Daily or Period-End or null if BEN",
  "ki_type": "Daily or EKI",
  "underlyings": [
    {{
      "ticker": "symbol",
      "spot_price": initial/strike price,
      "strike_price": strike or put strike,
      "ko_price": KO barrier price,
      "ki_price": KI barrier price
    }}
  ]
}}

IMPORTANT:
- For Phoenix: strike_price = Put Strike (typically 74.86% level)
- For BEN: strike_price = Strike for conversion (typically 88% level)
- For FCN: strike_price = same as spot_price usually
- All prices must be in dollars, not percentages
- Return ONLY valid JSON, no additional text

Termsheet text:
{pdf_text[:15000]}"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response
        response_text = message.content[0].text
        
        # Extract JSON from response
        if '{' in response_text and '}' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            extracted_data = json.loads(json_str)
            return extracted_data
        else:
            return None
            
    except Exception as e:
        print(f"Error with Claude API: {e}")
        return None


def extract_note_data_with_openai(pdf_text: str, api_key: str) -> Optional[Dict]:
    """
    Use OpenAI GPT-4 to extract structured note data from termsheet text
    
    Args:
        pdf_text: Text extracted from PDF
        api_key: OpenAI API key
    
    Returns:
        Dictionary with extracted note data
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a financial analyst extracting data from structured note termsheets. Return only valid JSON."},
                {"role": "user", "content": f"""Extract structured note data from this termsheet and return as JSON with these fields:
- customer_name, type_of_structured_product (FCN/Phoenix/BEN), notional_amount, isin
- trade_date, issue_date, observation_start_date, final_valuation_date (YYYY-MM-DD format)
- coupon_payment_dates (comma-separated YYYY-MM-DD), coupon_per_annum (decimal)
- coupon_barrier (price for Phoenix/BEN), ko_type, ki_type
- underlyings array with: ticker, spot_price, strike_price, ko_price, ki_price

All prices in dollars, not percentages. Return ONLY JSON.

Termsheet:
{pdf_text[:12000]}"""}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data
        
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return None

