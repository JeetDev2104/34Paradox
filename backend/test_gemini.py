#!/usr/bin/env python3
"""
Test script to verify Gemini API key is working correctly
"""

import google.generativeai as genai
import os
import sys

def test_gemini_api():
    print("Testing Gemini API integration...")
    
    # Try to load the API key from .env.gemini file
    key_file_path = os.path.join(os.path.dirname(__file__), ".env.gemini")
    
    if os.path.exists(key_file_path):
        with open(key_file_path, "r") as f:
            api_key = f.read().strip()
            print("✓ Found API key in .env.gemini file")
    else:
        print("✗ Could not find .env.gemini file")
        return False
    
    if not api_key:
        print("✗ API key is empty")
        return False
    
    try:
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        print("✓ Successfully configured Gemini API client")
        
        # Choose a current working model
        model_name = "models/gemini-1.5-flash"
        print(f"\nUsing model: {model_name}")
        
        # Test by creating a model instance
        model = genai.GenerativeModel(model_name)
        print("✓ Successfully created Gemini model instance")
        
        # Simple test prompt
        response = model.generate_content("What is the capital of France?")
        print("✓ Successfully called Gemini API")
        print("\nTest response:")
        print(response.text)
        
        print("\nGemini API integration is working correctly!")
        return True
    except Exception as e:
        print(f"✗ Error testing Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_api() 