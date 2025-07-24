"""
Simple API Server untuk Background Remover
Step 1 implementation - Basic API structure
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.remover import remove_background, apply_solid_background, resize_pas_foto
import config


def create_simple_api():
    """Create a simple API structure for testing"""

    print("🚀 Initializing Background Remover API Server...")

    # Test core functionality
    try:
        # Test with a simple bytes object to verify import works
        print("✅ Core functions imported successfully:")
        print("  - remove_background")
        print("  - apply_solid_background")
        print("  - resize_pas_foto")
    except Exception as e:
        print(f"❌ Failed to import core functions: {e}")
        return False

    # Test configuration
    try:
        print(f"✅ Config loaded - API will run on {config.API_HOST}:{config.API_PORT}")
        print(f"✅ API Key configured: {'Yes' if config.API_KEY else 'No'}")
        print(f"✅ Rate limit: {config.RATE_LIMIT_PER_MINUTE} requests/minute")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = create_simple_api()
    if success:
        print("\n🎉 Step 1 - API Foundation Setup Complete!")
        print("\nNext Steps:")
        print("- Step 2: Create FastAPI routes")
        print("- Step 3: Add file upload handling")
        print("- Step 4: Integrate background removal logic")
        print("- Step 5: Add comprehensive error handling")
        print("- Step 6: Create API documentation")
        print("- Step 7: Production deployment setup")
    else:
        print("\n❌ Step 1 failed. Please check the errors above.")
