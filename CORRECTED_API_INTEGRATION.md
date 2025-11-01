# Corrected Sphero API Integration Guide

Based on Claude 4.5's research into the actual spherov2.py API documentation AND sleep mode handling, here are the key corrections and improvements needed for your Sphero AI Assistant.

## 🚨 CRITICAL INSIGHT: Sleep Mode vs Wake Mode

**Claude's Key Discovery**: When Sphero comes off the charger, it enters SLEEP MODE:
- Sleep mode = DARK and QUIET but Bluetooth is ACTIVE
- You do NOT need to shake it or wake it up
- Just scan for it and connect - it's listening!

This explains why many connection attempts fail - people think the Sphero is "off" when it's actually in sleep mode and ready to connect.

## Key API Corrections Found

### 1. Matrix Methods (Sphero Bolt Only)
Your current code was missing the actual matrix API methods:

```python
# ❌ Old (missing matrix functionality)
sphero_api.set_main_led(Color(255, 0, 0))

# ✅ New (with matrix support)
sphero_api.set_matrix_pixel(x, y, Color(r, g, b))
sphero_api.scroll_matrix_text("HELLO", Color(255, 255, 255), 30)
sphero_api.set_matrix_character('A', Color(0, 255, 0))
sphero_api.clear_matrix()
```

### 2. Event-Driven Controller Mode
The real API supports event handlers for interactive control:

```python
# ✅ Event handlers (missing from your current implementation)
sphero_api.on_collision = self._handle_collision
sphero_api.on_gyro_max = self._handle_gyro_max  # Spin detection
sphero_api.on_freefall = self._handle_freefall
sphero_api.on_landing = self._handle_landing

# Disable stabilization for better event detection
sphero_api.set_stabilization(False)
```

### 3. Real Sensor Methods
Actual documented sensor methods:

```python
# ✅ Real sensor API methods
heading = sphero_api.get_heading()
acceleration = sphero_api.get_acceleration()
gyroscope = sphero_api.get_gyroscope()
velocity = sphero_api.get_velocity()
position = sphero_api.get_position()
```

### 4. Context Manager Usage
Proper connection handling:

```python
# ✅ Correct context manager usage
with target_toy:
    sphero_api = SpheroEduAPI(target_toy)
    # All operations here
```

## Integration Steps

### Step 1: Test Claude's Method First
```bash
python test_claude_sphero_method.py
```

This implements Claude's complete methodology including sleep mode handling.

### Step 2: Test the Corrected API
```bash
python test_corrected_sphero_api.py
```

This will test all the corrected API methods and show you what's working.

### Step 2: Update Your Enhanced Controller
Replace the LED-only methods in `enhanced_sphero_controller.py` with the matrix-capable methods from `corrected_sphero_controller.py`.

Key changes needed:
- Add matrix support detection (`has_matrix` flag)
- Add event handler registration methods
- Add real sensor monitoring
- Update LED expression methods to use matrix when available

### Step 3: Update LED Expression Manager
Enhance `led_expression_manager.py` to use matrix display:

```python
async def express_emotion_with_matrix(self, emotion: EmotionType, message: str = None):
    """Express emotion using both LED and matrix"""
    if self.sphero_controller.has_matrix and message:
        await self.sphero_controller.display_matrix_text(message, color)
    else:
        # Fallback to LED-only
        await self.sphero_controller.set_main_led(color)
```

### Step 4: Add AI Response System
The new `SpheroAIResponder` class shows how the AI can "talk back" through the matrix:

```python
# AI responds to user interactions
ai_responder = SpheroAIResponder(controller)
await ai_responder.respond_to_user("HELLO", "happy")
```

## New Capabilities Unlocked

### 1. Matrix Communication
- Display text messages from AI
- Show status indicators
- Create custom patterns and animations
- Visual feedback for AI states

### 2. Event-Driven Interaction
- Collision detection → AI responds with "OUCH!"
- Spin detection → AI responds with "WHEE!"
- Freefall detection → AI responds with "HELP!"
- Landing detection → AI responds with "SAFE!"

### 3. Real Sensor Integration
- Continuous heading, acceleration, gyroscope monitoring
- Position and velocity tracking
- Context-aware AI responses based on movement

### 4. Controller Mode
- Sphero becomes an expressive input device
- AI uses matrix to communicate back
- Perfect for interactive AI assistant scenarios

## Testing Checklist

- [ ] Basic LED control works
- [ ] Matrix pixel setting works (Bolt only)
- [ ] Matrix text scrolling works (Bolt only)
- [ ] Matrix character display works (Bolt only)
- [ ] Collision events trigger AI responses
- [ ] Spin events trigger AI responses
- [ ] Sensor data updates continuously
- [ ] AI can respond with matrix messages
- [ ] Custom matrix patterns display correctly

## Troubleshooting

### Matrix Not Working
- Ensure you have a Sphero Bolt (not Mini/SPRK+)
- Check `controller.has_matrix` is True
- Verify connection is stable

### Events Not Firing
- Spin HARD (needs >5.5 rotations/sec for gyro_max)
- Tap firmly for collision detection
- Ensure stabilization is disabled

### Connection Issues
- Sphero must be ON but NOT paired in Windows
- Remove from Windows Bluetooth settings if paired
- Ensure no other apps are connected

## Next Steps

1. Run the test script to verify everything works
2. Integrate the corrected methods into your existing controllers
3. Update your AI agent to use matrix communication
4. Add event-driven AI personality responses
5. Create custom matrix patterns for different AI states

The corrected API transforms your Sphero from a simple LED indicator into a rich, interactive communication device for your AI assistant!
## Cla
ude's Sleep Mode Connection Method

### The Problem
Most Sphero connection failures happen because people don't understand sleep mode:

```python
# ❌ Wrong assumption
# "Sphero is dark and quiet, so it must be off"
# → Try to wake it up, shake it, etc.

# ✅ Claude's insight
# "Sphero is dark and quiet because it's in SLEEP MODE"
# → Bluetooth is active, just scan and connect!
```

### Claude's Robust Connection Process

```python
# 1. Pre-connection checklist
logger.info("📋 PRE-CONNECTION CHECKLIST:")
logger.info("   ✓ Sphero was recently on charger (saw SB-5925?)")
logger.info("   ✓ Sphero is now OFF charger") 
logger.info("   ✓ Sphero appears dark/quiet (SLEEP mode - normal!)")
logger.info("   ✓ Bluetooth is enabled")

# 2. Scan with proper expectations
logger.info("🔍 Scanning for Sphero Bolt...")
logger.info("   The robot doesn't need to show lights - it's listening!")

# 3. Connect and wake up with feedback
with toy:
    api = SpheroEduAPI(toy)
    
    # Wake up with visual confirmation
    api.set_main_led(Color(0, 255, 0))  # Green = connected
    api.set_matrix_character("✓", Color(0, 255, 0))  # Checkmark
    api.scroll_matrix_text("READY", Color(0, 255, 255), fps=8)
```

### Integration with Your Existing System

Replace your current connection logic in `enhanced_sphero_controller.py`:

```python
# ❌ Replace this
async def _connect_to_sphero(self, target_name: str = None) -> bool:
    toys = scanner.find_toys(timeout=15)
    # ... existing logic

# ✅ With Claude's method
async def _claude_find_and_connect(self, timeout: int) -> bool:
    # Implement Claude's sleep mode aware connection
    # See claude_corrected_controller.py for full implementation
```

## Event-Driven AI Personality

Claude's method enables true interactive AI personality:

```python
# Register event handlers
api.register_event(EventType.on_collision, self._handle_collision)
api.register_event(EventType.on_gyro_max, self._handle_gyro_max)

# Disable stabilization for better event detection
api.set_stabilization(False)

def _handle_collision(self, api):
    """AI responds with personality"""
    api.set_main_led(Color(255, 0, 0))
    api.scroll_matrix_text("OW!", Color(255, 0, 0), fps=15)
    print("💥 AI: That hurt!")

def _handle_gyro_max(self, api):
    """AI responds to spinning"""
    api.scroll_matrix_text("WHEE!", Color(0, 255, 255), fps=15)
    print("🌀 AI: I'm dizzy!")
```

## Troubleshooting with Claude's Insights

### Connection Fails
1. **Put Sphero back on charger for 3 seconds**
2. **Watch for robot ID display (like SB-5925)**
3. **Remove from charger**
4. **Wait 5 seconds, then scan immediately**

### No Events Firing
- **Spin HARD** (needs >5.5 rotations/sec for gyro_max)
- **Tap firmly** for collision detection
- **Ensure stabilization is disabled**

### Matrix Not Working
- **Verify it's a Sphero Bolt** (not Mini/SPRK+)
- **Check `has_matrix` flag is True**
- **Test with simple character first**

## Quick Start with Claude's Method

```bash
# 1. Test Claude's connection method
python test_claude_sphero_method.py

# 2. If that works, integrate into your system
# Replace connection logic in enhanced_sphero_controller.py
# with claude_corrected_controller.py methods

# 3. Add AI personality responses
# Use ClaudeAIResponder as example
```

The key insight is that **sleep mode is normal and expected** - don't fight it, work with it!