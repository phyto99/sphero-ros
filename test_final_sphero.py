"""
Test Final Sphero Controller - Simple test to identify connection issues
"""

import logging
from sphero_ai_assistant.sphero.final_sphero_controller import FinalSpheroController

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the final controller"""
    logger.info("=== Final Sphero Controller Test ===")
    logger.info("We know SB-5925 is found by scanner, testing controller...")
    
    # Use the known working robot ID
    robot_id = "SB-5925"
    logger.info(f"Testing with: {robot_id}")
    
    controller = FinalSpheroController()
    
    try:
        # Connect
        logger.info("Attempting connection...")
        if controller.connect(robot_id, timeout=30):
            logger.info("✅ Connection successful!")
            
            # Test functionality
            if controller.test_functionality():
                logger.info("✅ All functionality works!")
                
                # Demo AI expressions
                logger.info("Testing AI expressions...")
                controller.ai_thinking()
                controller.ai_ready()
                
                logger.info("🎉 SUCCESS! Controller is working perfectly.")
                return True
            else:
                logger.error("❌ Functionality test failed")
        else:
            logger.error("❌ Connection failed")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        controller.disconnect()

if __name__ == "__main__":
    success = main()
    
    if not success:
        logger.info("\n🔧 NEXT STEPS:")
        logger.info("1. Run: python basic_sphero_test.py")
        logger.info("2. Check if scanner finds any devices")
        logger.info("3. If no devices found:")
        logger.info("   - Put Sphero on charger for 3 seconds")
        logger.info("   - Remove from charger")
        logger.info("   - Make sure NOT paired in Windows")
        logger.info("   - Try again")