# Sphero Bolt Testing Guide

## Prerequisites

### 1. Install Sphero SDK
First, you need to install the Sphero SDK for Python:

```bash
pip install spherov2
```

### 2. Prepare Your Sphero Bolt
1. **Charge your Sphero Bolt** - Make sure it has at least 50% battery
2. **Turn on your Sphero Bolt** - Press and hold the power button until it lights up
3. **Enable Bluetooth** on your computer
4. **Put Sphero in pairing mode** - The Sphero should automatically be discoverable when turned on

### 3. Bluetooth Setup (Windows)
1. Open Windows Settings > Devices > Bluetooth & other devices
2. Make sure Bluetooth is turned on
3. Your Sphero should appear in the list of available devices
4. **DO NOT pair it through Windows** - the Python SDK will handle the connection

## Testing Steps

### Step 1: Start the AI Assistant
```bash
python -m sphero_ai_assistant.main
```

This will:
- Start all system components
- Launch the dashboard at http://127.0.0.1:8000
- Initialize the Sphero controller (in simulation mode initially)
- Show the Sphero simulator window (if no real Sphero is connected)

### Step 2: Access the Dashboard
1. Open your web browser
2. Go to http://127.0.0.1:8000
3. You should see the dashboard with a "Sphero Control" panel

### Step 3: Connect to Your Real Sphero Bolt
1. **Turn on your Sphero Bolt** and make sure it's nearby (within 10 feet)
2. In the Sphero Control panel, click **"Connect Sphero"**
3. The system will:
   - Scan for available Sphero devices (this takes ~10-15 seconds)
   - Show you a list if multiple Spheros are found
   - Let you choose which Sphero to connect to
4. If successful, you'll see:
   - Connection status changes to "Connected to [Sphero Name]"
   - Real battery level displays
   - Test LED button becomes enabled
   - Your Sphero will briefly flash green to confirm connection

### Step 4: Test Basic Functions
1. **Test LED**: Click the "Test LED" button - your Sphero should light up green briefly
2. **Check Status**: The dashboard should show real battery level and connection status
3. **AI Expression**: The AI can now express emotions through your real Sphero

### Step 5: Test AI Integration
Run the comprehensive test script:
```bash
python test_sphero_integration.py
```

This will test:
- LED expressions (happy, thinking, etc.)
- AI state communication
- Message notifications
- Custom patterns

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Sphero"
**Solutions**:
1. Make sure Sphero is turned on and charged
2. Check that Bluetooth is enabled on your computer
3. Try turning Sphero off and on again
4. Make sure no other apps are connected to the Sphero
5. Try running as administrator (Windows)

**Problem**: "No Sphero devices found"
**Solutions**:
1. Make sure Sphero is turned on and charged (should be glowing, not blinking)
2. **IMPORTANT**: Make sure Sphero is NOT paired in Windows Bluetooth settings (unpair if it is)
3. Move Sphero closer to your computer (within 5 feet)
4. Try turning Sphero off and on again (hold power button for 3 seconds)
5. Make sure no other apps (like Sphero Edu) are connected to the Sphero
6. Check Windows Device Manager for Bluetooth issues
7. Restart Bluetooth service: `services.msc` → Bluetooth Support Service → Restart
8. Try running as administrator (Windows)

### SDK Issues

**Problem**: "spherov2 module not found"
**Solution**:
```bash
pip install spherov2
```

**Problem**: "Permission denied" or "Access denied"
**Solutions**:
1. Run command prompt as Administrator
2. On Windows, you might need to install Visual C++ Build Tools
3. Try: `pip install --user spherov2`

### Performance Issues

**Problem**: Slow response or lag
**Solutions**:
1. Make sure Sphero is close to your computer (within 10 feet)
2. Close other Bluetooth applications
3. Check battery level - low battery can cause performance issues

## Advanced Testing

### Custom LED Patterns
You can test custom patterns through the Python console:

```python
import asyncio
from sphero_ai_assistant.sphero import EmotionType, ExpressionPattern

# Assuming you have the AI agent running
async def test_custom_patterns():
    # Express different emotions
    await ai_agent.express_ai_emotion('happy', intensity=0.8)
    await asyncio.sleep(3)
    
    await ai_agent.express_ai_emotion('thinking', intensity=0.6)
    await asyncio.sleep(3)
    
    await ai_agent.express_ai_emotion('excited', intensity=1.0)
    await asyncio.sleep(3)

# Run the test
asyncio.run(test_custom_patterns())
```

### Movement Testing
```python
# Test movement (be careful - make sure Sphero has space to move!)
async def test_movement():
    if ai_agent.sphero_controller:
        await ai_agent.sphero_controller.add_task(
            'movement',
            priority=5,
            duration=2.0,
            data={
                'movement': {
                    'direction': 0,    # North
                    'speed': 50,       # Medium speed
                }
            }
        )

asyncio.run(test_movement())
```

## Expected Behavior

### Successful Connection
- Dashboard shows "Connected" status
- Battery level displays (e.g., "85.3%")
- Sphero LED briefly flashes green
- Test LED button works
- AI can express emotions through Sphero

### AI Expression Examples
- **Happy**: Green pulsing light
- **Thinking**: Purple thinking dots pattern
- **Working**: Blue wave pattern
- **Excited**: Rainbow celebration pattern
- **Concerned**: Orange/red alert pattern

### Autonomous Behavior
The AI should automatically:
- Monitor battery level
- Prioritize tasks based on importance
- Express emotions based on system state
- Handle multiple simultaneous requests
- Gracefully degrade when battery is low

## Safety Notes

1. **Clear Space**: Make sure Sphero has clear space to move (at least 3x3 feet)
2. **Battery**: Don't let battery go below 10% during testing
3. **Surface**: Test on smooth, flat surfaces only
4. **Supervision**: Always supervise when testing movement commands

## Logging and Debugging

Check the log file for detailed information:
- Log file: `sphero_ai_assistant.log`
- Look for entries with "sphero" or "Sphero" in them
- Connection attempts, battery levels, and errors are logged

## Next Steps

Once basic connection works, you can:
1. Test the AI task assistance features
2. Experiment with different LED expressions
3. Test the autonomous decision-making
4. Try the multilingual communication features
5. Test the monitoring and productivity features

## Support

If you encounter issues:
1. Check the log file for error details
2. Try the troubleshooting steps above
3. Make sure your Sphero Bolt firmware is up to date
4. Test with the official Sphero Edu app first to ensure hardware works