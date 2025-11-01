"""
Sphero Bolt - LOW-LEVEL API DIRECT ACCESS
Bypassing SpheroEduAPI to access toy commands directly
Based on spherov2 documentation stating it uses pysphero functionality
"""

import time
import sys
import logging
from spherov2 import scanner
from spherov2.types import Color

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class SpheroBoltLowLevelDirect:
    """Direct access to toy object without SpheroEduAPI wrapper"""
    
    def __init__(self):
        self.toy = None
        self.connected = False
    
    def connect(self, robot_id="SB-5925", scan_timeout=8):
        """Connect directly to toy object"""
        print("\n" + "="*60)
        print("🔧 SPHERO BOLT - DIRECT LOW-LEVEL ACCESS")
        print("="*60)
        print("\n💡 Strategy: Bypass SpheroEduAPI, access toy directly")
        print("📋 Setup: Charger → Wait 2-3s → Remove → Wait 3s")
        
        input("\nPress Enter when ready...")
        
        print(f"\n🔍 Scanning for {robot_id}...")
        
        try:
            toys = scanner.find_toys(timeout=scan_timeout)
            
            if not toys:
                print("❌ No toys found")
                return False
            
            matching_toys = [t for t in toys if robot_id.upper() in t.name.upper()]
            
            if not matching_toys:
                print(f"❌ Found {len(toys)} toys but none match '{robot_id}'")
                for toy in toys:
                    print(f"   - {toy.name}")
                return False
            
            self.toy = matching_toys[0]
            print(f"✅ Found: {self.toy.name}")
            
        except Exception as e:
            print(f"❌ Scan error: {e}")
            return False
        
        print(f"\n🔗 Connecting to toy object...")
        
        try:
            # Connect to the toy directly
            self.toy.__enter__()
            print(f"✅ Connected to toy: {type(self.toy)}")
            
            self.connected = True
            
            # Wait for initialization
            print(f"\n⏳ Waiting for initialization...")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def explore_toy_object(self):
        """Explore what's available on the toy object"""
        print("\n" + "="*60)
        print("🔬 EXPLORING TOY OBJECT")
        print("="*60)
        
        print(f"\n📋 Toy object type: {type(self.toy)}")
        print(f"📋 Toy object attributes:")
        
        attrs = [a for a in dir(self.toy) if not a.startswith('_')]
        
        # Group attributes by type
        methods = []
        properties = []
        
        for attr in attrs:
            try:
                obj = getattr(self.toy, attr)
                if callable(obj):
                    methods.append(attr)
                else:
                    properties.append(attr)
            except:
                properties.append(attr)
        
        print(f"\n🔧 Methods ({len(methods)}):")
        for method in sorted(methods)[:20]:  # Show first 20
            print(f"   - {method}()")
        if len(methods) > 20:
            print(f"   ... and {len(methods) - 20} more")
        
        print(f"\n📊 Properties ({len(properties)}):")
        for prop in sorted(properties)[:15]:  # Show first 15
            print(f"   - {prop}")
        if len(properties) > 15:
            print(f"   ... and {len(properties) - 15} more")
        
        # Look for LED/matrix related attributes
        led_attrs = [a for a in attrs if 'led' in a.lower()]
        matrix_attrs = [a for a in attrs if 'matrix' in a.lower() or 'anim' in a.lower()]
        
        if led_attrs:
            print(f"\n💡 LED-related attributes:")
            for attr in led_attrs:
                print(f"   - {attr}")
        
        if matrix_attrs:
            print(f"\n🎯 Matrix/Animation attributes:")
            for attr in matrix_attrs:
                print(f"   - {attr}")
        
        return attrs
    
    def test_direct_commands(self):
        """Test direct command methods"""
        print("\n" + "="*60)
        print("🧪 TESTING DIRECT COMMANDS")
        print("="*60)
        
        # Test 1: Look for send_command or similar
        if hasattr(self.toy, 'send_command'):
            print("\n[1] Found send_command method")
            try:
                print(f"   send_command signature: {self.toy.send_command.__doc__}")
            except:
                pass
        
        # Test 2: Look for LED control
        led_methods = [m for m in dir(self.toy) if 'led' in m.lower() and not m.startswith('_')]
        if led_methods:
            print(f"\n[2] Found LED methods: {led_methods}")
            
            for method_name in led_methods:
                try:
                    method = getattr(self.toy, method_name)
                    if callable(method):
                        print(f"\n   Testing {method_name}...")
                        print(f"   Signature: {method.__doc__ or 'No docs'}")
                        
                        # Try to call with basic parameters
                        if 'set' in method_name.lower():
                            try:
                                print(f"   Attempting to call {method_name} with red color...")
                                # Try different parameter combinations
                                try:
                                    method(255, 0, 0)  # RGB
                                    print(f"   ✅ {method_name}(255, 0, 0) - check for red LED")
                                    time.sleep(2)
                                except:
                                    try:
                                        method(Color(255, 0, 0))  # Color object
                                        print(f"   ✅ {method_name}(Color(255, 0, 0)) - check for red LED")
                                        time.sleep(2)
                                    except Exception as e:
                                        print(f"   ❌ {method_name} failed: {e}")
                            except Exception as e:
                                print(f"   ❌ Error calling {method_name}: {e}")
                except Exception as e:
                    print(f"   ❌ Error accessing {method_name}: {e}")
        
        # Test 3: Look for matrix/animation control
        matrix_methods = [m for m in dir(self.toy) if ('matrix' in m.lower() or 'anim' in m.lower()) and not m.startswith('_')]
        if matrix_methods:
            print(f"\n[3] Found matrix methods: {matrix_methods}")
            
            for method_name in matrix_methods:
                try:
                    method = getattr(self.toy, method_name)
                    if callable(method):
                        print(f"\n   Testing {method_name}...")
                        print(f"   Signature: {method.__doc__ or 'No docs'}")
                        
                        # Try basic matrix operations
                        if 'set' in method_name.lower() or 'show' in method_name.lower():
                            try:
                                print(f"   Attempting to call {method_name}...")
                                # Try different approaches
                                if 'char' in method_name.lower():
                                    method('A')
                                    print(f"   ✅ {method_name}('A') - check for 'A' on matrix")
                                    time.sleep(2)
                                elif 'text' in method_name.lower():
                                    method('HI')
                                    print(f"   ✅ {method_name}('HI') - check for 'HI' on matrix")
                                    time.sleep(2)
                                else:
                                    # Try generic call
                                    method()
                                    print(f"   ✅ {method_name}() called")
                                    time.sleep(1)
                            except Exception as e:
                                print(f"   ❌ Error calling {method_name}: {e}")
                except Exception as e:
                    print(f"   ❌ Error accessing {method_name}: {e}")
    
    def test_command_sending(self):
        """Test sending raw commands if available"""
        print("\n" + "="*60)
        print("🚀 TESTING RAW COMMAND SENDING")
        print("="*60)
        
        # Look for command sending methods
        command_methods = []
        for attr in dir(self.toy):
            if any(word in attr.lower() for word in ['command', 'send', 'write', 'execute']):
                if not attr.startswith('_') and callable(getattr(self.toy, attr, None)):
                    command_methods.append(attr)
        
        if command_methods:
            print(f"\nFound command methods: {command_methods}")
            
            for method_name in command_methods:
                try:
                    method = getattr(self.toy, method_name)
                    print(f"\n📋 {method_name}:")
                    print(f"   Signature: {method.__doc__ or 'No documentation'}")
                    
                    # Don't actually call these without knowing parameters
                    print(f"   → Available for manual testing")
                    
                except Exception as e:
                    print(f"   ❌ Error accessing {method_name}: {e}")
        else:
            print("\n❌ No command sending methods found")
    
    def interactive_exploration(self):
        """Interactive exploration mode"""
        print("\n" + "="*60)
        print("🎮 INTERACTIVE EXPLORATION")
        print("="*60)
        print("\nYou can now manually test methods:")
        print("  - Type 'help' for available commands")
        print("  - Type 'quit' to exit")
        print("  - Type method names to try them")
        
        attrs = [a for a in dir(self.toy) if not a.startswith('_')]
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    break
                elif cmd.lower() == 'help':
                    print("\nAvailable attributes:")
                    for attr in sorted(attrs)[:20]:
                        print(f"  - {attr}")
                    if len(attrs) > 20:
                        print(f"  ... and {len(attrs) - 20} more")
                elif cmd in attrs:
                    try:
                        obj = getattr(self.toy, cmd)
                        if callable(obj):
                            print(f"\n{cmd} is a method")
                            print(f"Doc: {obj.__doc__ or 'No documentation'}")
                            
                            call_it = input("Call it? (y/n): ")
                            if call_it.lower() == 'y':
                                try:
                                    result = obj()
                                    print(f"Result: {result}")
                                except Exception as e:
                                    print(f"Error: {e}")
                        else:
                            print(f"\n{cmd} = {obj}")
                    except Exception as e:
                        print(f"Error accessing {cmd}: {e}")
                else:
                    print(f"Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                break
    
    def disconnect(self):
        """Disconnect"""
        if self.connected:
            try:
                print("\n👋 Disconnecting...")
                self.toy.__exit__(None, None, None)
                print("✅ Disconnected")
            except Exception as e:
                print(f"⚠️  Disconnect error: {e}")
            self.connected = False


def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("🔧 SPHERO BOLT - LOW-LEVEL DIRECT ACCESS")
    print("="*60)
    print("\n💡 This version:")
    print("  • Connects directly to toy object")
    print("  • Bypasses SpheroEduAPI wrapper")
    print("  • Explores all available methods")
    print("  • Tests direct command access")
    print("\n")
    
    input("Press Enter to start...")
    
    tester = SpheroBoltLowLevelDirect()
    
    try:
        if not tester.connect(robot_id="SB-5925"):
            print("\n❌ Failed to connect")
            return
        
        # Explore the toy object
        tester.explore_toy_object()
        
        input("\nPress Enter to test direct commands...")
        
        # Test direct commands
        tester.test_direct_commands()
        
        input("\nPress Enter to test raw command sending...")
        
        # Test command sending
        tester.test_command_sending()
        
        input("\nPress Enter for interactive exploration...")
        
        # Interactive mode
        tester.interactive_exploration()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tester.disconnect()


if __name__ == "__main__":
    main()