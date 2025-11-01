"""
Sphero Bolt - FINAL SOLUTION ATTEMPT
Direct toy object access + alternative command methods
"""

import time
import sys
import logging
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI, EventType
from spherov2.types import Color

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class SpheroBoltFinalFix:
    """Final attempt using all available methods"""
    
    def __init__(self):
        self.toy = None
        self.api = None
        self.connected = False
        self.working_led_method = None
        self.working_matrix_method = None
        self.event_counts = {
            'collision': 0,
            'spin': 0,
            'freefall': 0,
            'landing': 0
        }
        self.last_accel = {'x': 0, 'y': 0, 'z': 0}
        self.last_gyro = {'x': 0, 'y': 0, 'z': 0}
        self.accel_baseline = {'x': 0, 'y': 0, 'z': 9.81}
        self.accel_history = []
    
    def wait_for_full_wake(self, wait_seconds=3):
        """Wait for full initialization"""
        print(f"\n⏳ Waiting {wait_seconds}s for initialization...")
        for i in range(wait_seconds):
            print(f"   {'█' * (i+1)}{'░' * (wait_seconds-i-1)} {i+1}/{wait_seconds}s")
            time.sleep(1)
        print("✅ Ready\n")
    
    def connect(self, robot_id="SB-5925", scan_timeout=8, max_attempts=3):
        """Connect to Sphero"""
        print("\n" + "="*60)
        print("🔌 SPHERO BOLT - FINAL DIAGNOSTIC & FIX")
        print("="*60)
        print("\n📋 Setup: Charger → Wait 2-3s → Remove → Wait 3s")
        
        input("\nPress Enter when ready...")
        
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"\n{'='*60}")
            print(f"🔄 ATTEMPT #{attempt}/{max_attempts}")
            print('='*60)
            
            print(f"\n[1/3] 🔍 Scanning...")
            
            try:
                toys = scanner.find_toys(timeout=scan_timeout)
                
                if not toys:
                    if attempt < max_attempts:
                        time.sleep(5)
                        continue
                    return False
                
                matching_toys = [t for t in toys if robot_id.upper() in t.name.upper()]
                
                if not matching_toys:
                    if attempt < max_attempts:
                        time.sleep(5)
                        continue
                    return False
                
                self.toy = matching_toys[0]
                print(f"✅ Found: {self.toy.name}")
                
            except Exception as e:
                print(f"❌ Scan error: {e}")
                if attempt < max_attempts:
                    time.sleep(5)
                    continue
                return False
            
            print(f"\n[2/3] ⏳ Waiting for initialization...")
            self.wait_for_full_wake(3)
            
            print(f"[3/3] 🔗 Connecting...")
            
            try:
                self.api = SpheroEduAPI(self.toy)
                self.api.__enter__()
                
                heading = self.api.get_heading()
                print(f"   ✓ Connected (heading: {heading}°)")
                
                self.connected = True
                
                print("\n" + "="*60)
                print("✅ CONNECTION SUCCESS!")
                print("="*60)
                
                time.sleep(0.5)
                self.calibrate_baseline()
                
                return True
                
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                
                if self.api:
                    try:
                        self.api.__exit__(None, None, None)
                    except:
                        pass
                    self.api = None
                
                if attempt < max_attempts:
                    time.sleep(5)
                    continue
                return False
        
        return False
    
    def deep_led_diagnostic(self):
        """Comprehensive LED diagnostic"""
        print("\n" + "="*60)
        print("🔬 DEEP LED DIAGNOSTIC")
        print("="*60)
        
        print("\n📋 Testing toy object access...")
        
        # Try to access underlying toy object
        toy_obj = None
        if hasattr(self.api, '_toy'):
            toy_obj = self.api._toy
            print(f"✅ Accessed _toy: {type(toy_obj)}")
        else:
            print("❌ No _toy attribute")
        
        if toy_obj:
            print(f"\n📋 Toy object attributes:")
            attrs = [a for a in dir(toy_obj) if not a.startswith('_')]
            for attr in attrs[:15]:  # Show first 15
                print(f"   - {attr}")
            if len(attrs) > 15:
                print(f"   ... and {len(attrs) - 15} more")
        
        # Test methods
        tests = []
        
        print("\n" + "="*60)
        print("🧪 LED METHOD TESTS")
        print("="*60)
        
        # Test 1: Standard set_main_led
        print("\n[1] api.set_main_led(Color(255, 0, 0)) - RED")
        try:
            self.api.set_main_led(Color(255, 0, 0))
            time.sleep(2)
            result = input("LED turned RED? (y/n): ")
            tests.append(("set_main_led", result.lower() == 'y'))
            if result.lower() == 'y':
                self.working_led_method = 'main_led'
        except Exception as e:
            print(f"Error: {e}")
            tests.append(("set_main_led", False))
        
        self.api.set_main_led(Color(0, 0, 0))
        time.sleep(0.5)
        
        # Test 2: Back LED (we know this works)
        print("\n[2] api.set_back_led(Color(0, 255, 0)) - GREEN")
        try:
            self.api.set_back_led(Color(0, 255, 0))
            time.sleep(2)
            result = input("Back LED turned GREEN? (y/n): ")
            tests.append(("set_back_led", result.lower() == 'y'))
            if result.lower() == 'y' and not self.working_led_method:
                self.working_led_method = 'back_led'
        except Exception as e:
            print(f"Error: {e}")
            tests.append(("set_back_led", False))
        
        self.api.set_back_led(Color(0, 0, 0))
        time.sleep(0.5)
        
        # Test 3: Front LED
        print("\n[3] api.set_front_led(Color(0, 0, 255)) - BLUE")
        try:
            self.api.set_front_led(Color(0, 0, 255))
            time.sleep(2)
            result = input("Front LED turned BLUE? (y/n): ")
            tests.append(("set_front_led", result.lower() == 'y'))
            if result.lower() == 'y' and not self.working_led_method:
                self.working_led_method = 'front_led'
        except Exception as e:
            print(f"Error: {e}")
            tests.append(("set_front_led", False))
        
        self.api.set_front_led(Color(0, 0, 0))
        time.sleep(0.5)
        
        # Test 4: Try toy object LED if available
        if toy_obj and hasattr(toy_obj, 'led'):
            print("\n[4] Trying toy.led methods...")
            try:
                led_obj = toy_obj.led
                print(f"LED object: {type(led_obj)}")
                led_methods = [m for m in dir(led_obj) if not m.startswith('_')]
                print(f"Methods: {led_methods}")
                
                # Try any set_* methods
                for method_name in led_methods:
                    if 'set' in method_name.lower() and 'led' in method_name.lower():
                        print(f"\nTrying toy.led.{method_name}()...")
                        result = input("Try this method? (y/n): ")
                        if result.lower() == 'y':
                            # User can manually test
                            pass
            except Exception as e:
                print(f"Error accessing toy.led: {e}")
        
        # Matrix tests
        print("\n" + "="*60)
        print("🧪 MATRIX METHOD TESTS")
        print("="*60)
        
        # Test 5: Matrix text
        print("\n[5] api.scroll_matrix_text('HI', Color(255, 255, 0))")
        try:
            self.api.scroll_matrix_text('HI', Color(255, 255, 0), fps=10, wait=True)
            time.sleep(0.5)
            result = input("'HI' scrolled on matrix? (y/n): ")
            tests.append(("scroll_matrix_text", result.lower() == 'y'))
            if result.lower() == 'y':
                self.working_matrix_method = 'text'
        except Exception as e:
            print(f"Error: {e}")
            tests.append(("scroll_matrix_text", False))
        
        time.sleep(0.5)
        
        # Test 6: Matrix character
        print("\n[6] api.set_matrix_character('A', Color(0, 255, 255))")
        try:
            self.api.set_matrix_character('A', Color(0, 255, 255))
            time.sleep(1.5)
            result = input("'A' appeared on matrix? (y/n): ")
            tests.append(("set_matrix_character", result.lower() == 'y'))
            if result.lower() == 'y' and not self.working_matrix_method:
                self.working_matrix_method = 'char'
        except Exception as e:
            print(f"Error: {e}")
            tests.append(("set_matrix_character", False))
        
        try:
            self.api.clear_matrix()
        except:
            pass
        
        # Results
        print("\n" + "="*60)
        print("📊 DIAGNOSTIC RESULTS")
        print("="*60)
        
        print("\nLED Tests:")
        for name, passed in [t for t in tests if 'led' in t[0].lower()]:
            status = "✅ WORKS" if passed else "❌ FAILED"
            print(f"  {status}: {name}")
        
        print("\nMatrix Tests:")
        for name, passed in [t for t in tests if 'matrix' in t[0].lower()]:
            status = "✅ WORKS" if passed else "❌ FAILED"
            print(f"  {status}: {name}")
        
        print(f"\n🎯 Working LED method: {self.working_led_method or 'NONE'}")
        print(f"🎯 Working matrix method: {self.working_matrix_method or 'NONE'}")
        
        if not self.working_led_method or self.working_led_method in ['back_led', 'front_led']:
            print("\n" + "="*60)
            print("⚠️  CONCLUSION")
            print("="*60)
            print("\nMain LED/Matrix do NOT work with spherov2 on Windows.")
            print("Only back/front LEDs work (aim lights).")
            print("\n🔧 SOLUTION: Switch to pysphero on Raspberry Pi")
            print("   You already have a Pi, and pysphero was specifically")
            print("   reverse-engineered for Bolt with working LED/matrix.")
            print("\n📦 Quick Pi setup:")
            print("   1. sudo apt-get install libgtk2.0-dev")
            print("   2. pip3 install pysphero")
            print("   3. Port your code (I can help with this!)")
            print("\nYour collision detection code is EXCELLENT and will")
            print("transfer perfectly - it's just sensor math!")
    
    def calibrate_baseline(self):
        """Calibrate baseline"""
        print("\n🎯 Calibrating...")
        samples = []
        for i in range(20):
            try:
                accel = self.api.get_acceleration()
                samples.append(accel)
                time.sleep(0.1)
            except:
                pass
        
        if len(samples) >= 10:
            self.accel_baseline = {
                'x': sum(s['x'] for s in samples) / len(samples),
                'y': sum(s['y'] for s in samples) / len(samples),
                'z': sum(s['z'] for s in samples) / len(samples)
            }
            print(f"✅ Baseline set")
    
    def detect_collision_smart(self):
        """Smart collision detection"""
        try:
            accel = self.api.get_acceleration()
            
            if self.last_accel['x'] != 0:
                jerk_x = abs((accel['x'] - self.accel_baseline['x']) - 
                            (self.last_accel['x'] - self.accel_baseline['x']))
                jerk_y = abs((accel['y'] - self.accel_baseline['y']) - 
                            (self.last_accel['y'] - self.accel_baseline['y']))
                jerk_z = abs((accel['z'] - self.accel_baseline['z']) - 
                            (self.last_accel['z'] - self.accel_baseline['z']))
                
                jerk_magnitude = (jerk_x**2 + jerk_y**2 + jerk_z**2)**0.5
                
                self.accel_history.append(jerk_magnitude)
                if len(self.accel_history) > 5:
                    self.accel_history.pop(0)
                
                if len(self.accel_history) >= 3:
                    recent_avg = sum(self.accel_history[:-1]) / (len(self.accel_history) - 1)
                    current_jerk = self.accel_history[-1]
                    
                    if current_jerk > 4.5 and recent_avg < 2.0:
                        self.accel_history.clear()
                        self.last_accel = accel
                        return True, current_jerk
            
            self.last_accel = accel
                
        except:
            pass
        
        return False, 0
    
    def detect_spin(self):
        """Detect spinning"""
        try:
            gyro = self.api.get_gyroscope()
            magnitude = (gyro['x']**2 + gyro['y']**2 + gyro['z']**2)**0.5
            self.last_gyro = gyro
            if magnitude > 900:
                return True, magnitude
        except:
            pass
        return False, 0
    
    def setup_events(self):
        """Setup events"""
        print("\n📡 Setting up events...")
        
        try:
            def on_freefall(api):
                self.event_counts['freefall'] += 1
                print(f"🪂 FREEFALL! (Total: {self.event_counts['freefall']})")
            self.api.register_event(EventType.on_freefall, on_freefall)
            print("✅ Freefall")
        except Exception as e:
            print(f"⚠️  Freefall: {e}")
        
        try:
            def on_landing(api):
                self.event_counts['landing'] += 1
                print(f"🛬 LANDING! (Total: {self.event_counts['landing']})")
            self.api.register_event(EventType.on_landing, on_landing)
            print("✅ Landing")
        except Exception as e:
            print(f"⚠️  Landing: {e}")
        
        try:
            self.api.set_stabilization(False)
            print("✅ Stabilization off")
        except:
            pass
    
    def interactive_mode(self):
        """Interactive mode with working features"""
        print("\n" + "="*60)
        print("🎮 INTERACTIVE MODE")
        print("="*60)
        print("\nDetection active:")
        print("  💥 Collision  🌀 Spin  🪂 Freefall  🛬 Landing")
        
        if self.working_led_method == 'back_led':
            print("\n💡 Using back LED for visual feedback")
        elif self.working_led_method == 'front_led':
            print("\n💡 Using front LED for visual feedback")
        else:
            print("\n⚠️  No LED feedback (LEDs don't work)")
        
        print("\nPress Ctrl+C to exit\n")
        
        last_collision_time = 0
        last_spin_time = 0
        
        try:
            counter = 0
            while True:
                current_time = time.time()
                
                if current_time - last_collision_time > 1.8:
                    is_collision, jerk = self.detect_collision_smart()
                    if is_collision:
                        self.event_counts['collision'] += 1
                        print(f"💥 COLLISION! Jerk: {jerk:.2f} (Total: {self.event_counts['collision']})")
                        
                        # Use working LED if available
                        if self.working_led_method == 'back_led':
                            try:
                                self.api.set_back_led(Color(255, 0, 0))
                                time.sleep(0.3)
                                self.api.set_back_led(Color(0, 0, 0))
                            except:
                                pass
                        elif self.working_led_method == 'front_led':
                            try:
                                self.api.set_front_led(Color(255, 0, 0))
                                time.sleep(0.3)
                                self.api.set_front_led(Color(0, 0, 0))
                            except:
                                pass
                        
                        last_collision_time = current_time
                
                if current_time - last_spin_time > 1.5:
                    is_spin, ang_vel = self.detect_spin()
                    if is_spin:
                        self.event_counts['spin'] += 1
                        print(f"🌀 SPIN! Velocity: {ang_vel:.0f}°/s (Total: {self.event_counts['spin']})")
                        last_spin_time = current_time
                
                if counter % 50 == 0:
                    try:
                        heading = self.api.get_heading()
                        total = sum(self.event_counts.values())
                        print(f"📊 H:{heading:3.0f}° Events:{total}")
                    except:
                        pass
                
                counter += 1
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping...")
    
    def disconnect(self):
        """Disconnect"""
        if self.connected:
            try:
                print("\n👋 Disconnecting...")
                if self.api:
                    self.api.__exit__(None, None, None)
                print("✅ Disconnected\n")
            except Exception as e:
                print(f"⚠️  Disconnect: {e}")
            self.connected = False


def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("🔬 SPHERO BOLT - FINAL DIAGNOSTIC")
    print("="*60)
    print("\nThis will:")
    print("  1. Test ALL available LED/matrix methods")
    print("  2. Determine what actually works")
    print("  3. Recommend next steps")
    print("\n")
    
    input("Press Enter to start...")
    
    tester = SpheroBoltFinalFix()
    
    try:
        if not tester.connect(robot_id="SB-5925"):
            print("\n❌ Failed to connect")
            return
        
        time.sleep(1)
        
        # Run complete diagnostic
        tester.deep_led_diagnostic()
        time.sleep(1)
        
        # Setup events
        tester.setup_events()
        time.sleep(1)
        
        # Interactive mode
        print("\n💡 Ready for interactive mode")
        input("Press Enter to continue...")
        tester.interactive_mode()
        
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