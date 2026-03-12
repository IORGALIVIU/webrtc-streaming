# 🤖 Robot Car Hardware Setup Guide

## 📦 Hardware Components

- **Raspberry Pi 5**
- **PCA9685 16-Channel PWM Driver** (I2C)
- **Servo Motor** (steering)
- **L298N H-Bridge Motor Driver** (Seed Studio)
- **2x DC Motors**
- **Power Supply** (suitable for motors)

---

## 🔌 Wiring Diagram

### Raspberry Pi 5 → PCA9685 (I2C)

| Pi Pin | PCA9685 Pin |
|--------|-------------|
| 3.3V   | VCC         |
| GND    | GND         |
| SDA    | SDA         |
| SCL    | SCL         |

**PCA9685 I2C Address:** 0x40 (default)

---

### PCA9685 → Servo Motor

| PCA9685 Channel | Wire | Servo Pin |
|-----------------|------|-----------|
| 0 (PWM)         | Yellow/White | Signal |
| V+ (external)   | Red | VCC (+5V) |
| GND             | Brown/Black | GND |

**Note:** Servo needs **external 5V power** (not from Pi)!

---

### PCA9685 → L298N H-Bridge

| PCA9685 Ch | L298N Pin | Description |
|------------|-----------|-------------|
| 1 (PWM)    | IN1       | Motor A Forward |
| 2 (PWM)    | IN2       | Motor A Backward |
| 3 (PWM)    | IN3       | Motor B Forward |
| 4 (PWM)    | IN4       | Motor B Backward |
| 5 (PWM)    | ENA       | Motor A Enable (optional) |
| 6 (PWM)    | ENB       | Motor B Enable (optional) |

### L298N → DC Motors

| L298N Pin | Motor |
|-----------|-------|
| OUT1      | Motor A (+) |
| OUT2      | Motor A (-) |
| OUT3      | Motor B (+) |
| OUT4      | Motor B (-) |

### L298N Power

| L298N Pin | Connection |
|-----------|------------|
| +12V      | Battery/Power Supply + |
| GND       | Battery/Power Supply - (and Pi GND) |
| +5V OUT   | DO NOT USE (remove jumper if present) |

**Important:** 
- **Common GND** between Pi, PCA9685, and L298N!
- Motors need **separate power supply** (6-12V depending on motors)

---

## ⚙️ Software Setup

### 1. Enable I2C

```bash
sudo raspi-config
# Interface Options → I2C → Enable → Reboot
```

### 2. Verify I2C

```bash
# Install tools:
sudo apt-get install -y i2c-tools

# Detect PCA9685 (should show 0x40):
sudo i2cdetect -y 1
```

Expected output:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --  ← HERE!
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --
```

### 3. Install Python Libraries

```bash
cd ~/sender

# Install Adafruit libraries:
pip3 install adafruit-circuitpython-pca9685 \
             adafruit-circuitpython-motor \
             --break-system-packages

# Or use requirements:
pip3 install -r requirements.txt --break-system-packages
```

---

## 🧪 Test Hardware

### Test 1: PCA9685 Detection

```bash
python3 -c "
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
print('✅ PCA9685 detected successfully!')
pca.deinit()
"
```

### Test 2: Servo Test

```bash
cd ~/sender
python3 robot_controller.py
```

**Expected behavior:**
1. Servo centers (0°)
2. Turns left (-45°)
3. Turns right (+45°)
4. Centers again
5. Motors forward slow
6. Motors forward fast
7. Motors stop
8. Motors backward
9. Stop and center

**Watch motors and servo physically move!**

---

## 🎮 Run with Hardware Control

```bash
cd ~/sender
python3 sender_mqtt.py \
    --camera \
    --server-ip 192.168.0.198 \
    --mqtt-broker 192.168.0.198
```

**Expected logs:**
```
✅ Robot hardware controller initialized
[MQTT] Mode changed to: MANUAL
[ROBOT] Updated: angle=45°, speed=50
```

---

## 🔧 Configuration

### Adjust Motor Channels

Edit `robot_controller.py`:

```python
controller = RobotCarController(
    servo_channel=0,      # Servo on channel 0
    motor_a_fwd=1,        # Motor A forward on channel 1
    motor_a_bwd=2,        # Motor A backward on channel 2
    motor_b_fwd=3,        # Motor B forward on channel 3
    motor_b_bwd=4,        # Motor B backward on channel 4
    motor_a_enable=5,     # Optional PWM speed
    motor_b_enable=6,     # Optional PWM speed
)
```

### Adjust Servo Range

```python
controller = RobotCarController(
    servo_min_angle=-90,   # Min servo angle
    servo_max_angle=90,    # Max servo angle
    servo_min_pulse=500,   # Min pulse width (µs)
    servo_max_pulse=2500,  # Max pulse width (µs)
)
```

### Reverse Motor Direction

If motors spin backward, swap channels:

```python
# Before (wrong direction):
motor_a_fwd=1, motor_a_bwd=2

# After (correct direction):
motor_a_fwd=2, motor_a_bwd=1  # Swapped!
```

---

## ⚠️ Troubleshooting

### PCA9685 Not Detected

```bash
# Check I2C is enabled:
ls /dev/i2c*  # Should see /dev/i2c-1

# Check permissions:
sudo usermod -a -G i2c $USER
# Logout and login again

# Check wiring:
# - SDA to SDA
# - SCL to SCL
# - VCC to 3.3V
# - GND to GND
```

### Servo Not Moving

- ✅ Check servo has **external 5V power**
- ✅ Verify servo wire on correct channel (0)
- ✅ Test with multimeter: Should see ~50Hz PWM signal
- ✅ Adjust pulse width range in code

### Motors Not Spinning

- ✅ Check L298N has **separate motor power** (6-12V)
- ✅ Verify **common GND** between all components
- ✅ Check motor wires are connected to OUT1-4
- ✅ Test manually: Connect IN1 to HIGH, IN2 to LOW → Motor A should spin

### Motors Spin Wrong Direction

Swap either:
1. Motor wires on L298N (OUT1 ↔ OUT2)
2. Software channels (motor_a_fwd ↔ motor_a_bwd)

### Low Power / Weak Motors

- ✅ Check battery voltage (should be 7-12V for most motors)
- ✅ Check battery capacity (needs high current for motors)
- ✅ Ensure motor power supply is separate from Pi
- ✅ Add capacitors across motor terminals (reduce noise)

---

## 🔒 Safety

⚠️ **IMPORTANT:**
- Always have **emergency stop** ready (power switch)
- Test on blocks before putting on floor
- Start with **low speeds** (20-30%)
- Ensure **common ground** between all components
- **Never** power motors from Pi's 5V rail!
- Use **external battery** for motors
- Add **fuse** to motor power supply

---

## 📊 Default Pin Mapping Summary

| Component | PCA9685 Channel | Description |
|-----------|----------------|-------------|
| Servo | 0 | Steering (-180° to +180°) |
| Motor A FWD | 1 | Motor A forward direction |
| Motor A BWD | 2 | Motor A backward direction |
| Motor B FWD | 3 | Motor B forward direction |
| Motor B BWD | 4 | Motor B backward direction |
| Motor A EN | 5 | (Optional) PWM speed control |
| Motor B EN | 6 | (Optional) PWM speed control |

**Channels 7-15:** Available for additional servos/motors!

---

## ✅ Quick Checklist

```
☐ I2C enabled on Pi
☐ PCA9685 detected at 0x40
☐ Servo has external 5V power
☐ Motors have external 6-12V power
☐ Common GND between all components
☐ Python libraries installed
☐ robot_controller.py test passes
☐ Servo moves when testing
☐ Motors spin when testing
☐ Emergency stop accessible
```

---

**Ready to drive your robot! 🚗💨**
