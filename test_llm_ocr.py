#!/usr/bin/env python3
"""
Test script for LLM-based OCR functionality in SISIMPUR.
This replaces the old test_easyocr.py script.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add the apps directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

def create_test_image():
    """Create a simple test image with Bengali and English text."""
    # Create a white image
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add test text
    test_text = [
        "1. What is the capital of Bangladesh?",
        "   a) Dhaka",
        "   b) Chittagong", 
        "   c) Sylhet",
        "   d) Rajshahi",
        "",
        "২. বাংলাদেশের রাজধানী কী?",
        "   ক) ঢাকা",
        "   খ) চট্টগ্রাম",
        "   গ) সিলেট", 
        "   ঘ) রাজশাহী"
    ]
    
    y_position = 30
    for line in test_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    return img

def test_llm_ocr():
    """Test the LLM-based OCR functionality."""
    print("🧪 Testing LLM-based OCR functionality...")
    
    try:
        # Import the LLM OCR function
        from brain.brain_engine.utils.ocr_utils import llm_ocr_extract
        print("✅ Successfully imported llm_ocr_extract")
        
        # Create a test image
        print("📝 Creating test image with Bengali and English text...")
        test_img = create_test_image()
        
        # Test English OCR
        print("🔍 Testing English OCR...")
        english_result = llm_ocr_extract(test_img, language_code="eng", is_question_paper=True)
        print("📄 English OCR Result:")
        print(english_result)
        print()
        
        # Test Bengali OCR
        print("🔍 Testing Bengali OCR...")
        bengali_result = llm_ocr_extract(test_img, language_code="ben", is_question_paper=True)
        print("📄 Bengali OCR Result:")
        print(bengali_result)
        print()
        
        # Verify results contain expected content
        success_indicators = [
            "capital" in english_result.lower() or "রাজধানী" in bengali_result,
            "dhaka" in english_result.lower() or "ঢাকা" in bengali_result,
            "bangladesh" in english_result.lower() or "বাংলাদেশ" in bengali_result
        ]
        
        if any(success_indicators):
            print("✅ LLM OCR test PASSED! Text extraction working correctly.")
            return True
        else:
            print("❌ LLM OCR test FAILED! Could not extract expected content.")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the project root directory.")
        return False
    except Exception as e:
        print(f"❌ Error during LLM OCR test: {e}")
        return False

def test_api_connection():
    """Test Google Gemini API connection."""
    print("🌐 Testing Google Gemini API connection...")
    
    try:
        from brain.brain_engine.utils.api_utils import api
        from brain.brain_engine.config import DEFAULT_GEMINI_MODEL
        
        # Simple text generation test
        response = api.generate_content(
            ["Say 'Hello from SISIMPUR LLM OCR!' in both English and Bengali."],
            model_name=DEFAULT_GEMINI_MODEL
        )
        
        if response and response.text:
            print("✅ Google Gemini API connection successful!")
            print(f"📝 Response: {response.text[:100]}...")
            return True
        else:
            print("❌ Google Gemini API returned empty response.")
            return False
            
    except Exception as e:
        print(f"❌ Google Gemini API connection failed: {e}")
        print("💡 Check your GOOGLE_API_KEY environment variable.")
        return False

def main():
    """Run all tests."""
    print("🚀 SISIMPUR LLM OCR Test Suite")
    print("=" * 50)
    
    # Check environment
    if not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment variables.")
        print("💡 Set it with: export GOOGLE_API_KEY='your-api-key'")
        print()
    
    # Run tests
    tests = [
        ("API Connection", test_api_connection),
        ("LLM OCR Functionality", test_llm_ocr)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! LLM OCR is working correctly.")
        print("🚀 Your SISIMPUR project is ready to use!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("💡 Make sure your Google API key is set and valid.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
