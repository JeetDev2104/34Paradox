#!/usr/bin/env python3
"""
A utility script to set the Gemini API key for NewsWise Financial
"""

import os
import sys

def set_gemini_key():
    """
    Set the Gemini API key from command-line input or environment variables
    """
    # Check if key is already set in environment
    env_key = os.environ.get("GEMINI_API_KEY")
    
    if len(sys.argv) > 1:
        # Get key from command line argument
        api_key = sys.argv[1]
        print("Using API key from command line argument")
    elif env_key:
        # Use key from environment
        api_key = env_key
        print("Using API key from GEMINI_API_KEY environment variable")
    else:
        # Prompt user for key
        api_key = input("Enter your Gemini API key: ")
        
    if not api_key:
        print("Error: No API key provided")
        return False
        
    # Save key to file
    key_file_path = os.path.join(os.path.dirname(__file__), ".env.gemini")
    with open(key_file_path, "w") as f:
        f.write(api_key)
        
    print(f"API key saved to {key_file_path}")
    print("Gemini API integration is now configured!")
    print("\nYou can start the server with:")
    print("uvicorn main:app --reload --port 8000")
    
    return True

if __name__ == "__main__":
    set_gemini_key() 