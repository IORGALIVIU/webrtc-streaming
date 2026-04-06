#!/usr/bin/env python3
"""
Game-like keyboard controller for angle and speed
Smooth acceleration/deceleration like racing games
"""

import time
import threading


class GamepadController:
    """
    Simulates gamepad/racing game controls using keyboard.
    
    Features:
    - Smooth acceleration when holding keys
    - Quick response to rapid taps
    - Auto-deceleration when released
    - Opposite direction instantly reverses
    """
    
    def __init__(self, 
                 angle_max=60, angle_min=-60,
                 speed_max=100, speed_min=-100,  # Allow negative speed!
                 accel_rate=90.0,      # Units/second when holding
                 decel_rate=90.0,      # Units/second when released
                 quick_tap_boost=10.0  # Instant change for quick taps
                ):
        # Limits
        self.angle_max = angle_max
        self.angle_min = angle_min
        self.speed_max = speed_max
        self.speed_min = speed_min
        
        # Acceleration/deceleration rates
        self.accel_rate = accel_rate
        self.decel_rate = decel_rate
        self.quick_tap_boost = quick_tap_boost
        
        # Current values
        self.angle = 0.0
        self.speed = 0.0
        
        # Key states
        self.keys_pressed = {
            'left': False,
            'right': False,
            'up': False,
            'down': False
        }
        
        # Velocities (rate of change)
        self.angle_velocity = 0.0
        self.speed_velocity = 0.0
        
        # Last key press times (for detecting quick taps)
        self.last_key_time = {
            'left': 0,
            'right': 0,
            'up': 0,
            'down': 0
        }
        
        # Update thread
        self.running = False
        self.update_thread = None
        self.lock = threading.Lock()
    
    def start(self):
        """Start update thread."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
    
    def stop(self):
        """Stop update thread."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def key_press(self, key):
        """Handle key press."""
        current_time = time.time()
        
        with self.lock:
            if key in self.keys_pressed:
                # Check for quick tap (< 0.2s since last press)
                time_since_last = current_time - self.last_key_time[key]
                is_quick_tap = time_since_last > 0.2 and time_since_last < 0.5
                
                self.keys_pressed[key] = True
                self.last_key_time[key] = current_time
                
                # Apply quick tap boost
                if is_quick_tap:
                    if key == 'left':
                        self.angle = max(self.angle_min, self.angle - self.quick_tap_boost)
                    elif key == 'right':
                        self.angle = min(self.angle_max, self.angle + self.quick_tap_boost)
                    elif key == 'up':
                        self.speed = min(self.speed_max, self.speed + self.quick_tap_boost)
                    elif key == 'down':
                        self.speed = max(self.speed_min, self.speed - self.quick_tap_boost)
    
    def key_release(self, key):
        """Handle key release."""
        with self.lock:
            if key in self.keys_pressed:
                self.keys_pressed[key] = False
    
    def _update_loop(self):
        """Update loop - runs at ~60 FPS for smooth control."""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Cap dt to prevent huge jumps
            dt = min(dt, 0.1)
            
            with self.lock:
                self._update(dt)
            
            # Sleep to maintain ~60 FPS
            time.sleep(0.016)  # ~60 FPS
    
    def _update(self, dt):
        """Update angle and speed based on key states."""
        # ===== ANGLE CONTROL =====
        if self.keys_pressed['left'] and not self.keys_pressed['right']:
            # Accelerate left
            # If currently going right, accelerate FASTER (reverse boost)
            if self.angle > 0:
                self.angle_velocity = -self.accel_rate * 2.0  # 2x faster reverse!
            else:
                self.angle_velocity = -self.accel_rate
        elif self.keys_pressed['right'] and not self.keys_pressed['left']:
            # Accelerate right
            # If currently going left, accelerate FASTER (reverse boost)
            if self.angle < 0:
                self.angle_velocity = self.accel_rate * 2.0  # 2x faster reverse!
            else:
                self.angle_velocity = self.accel_rate
        elif self.keys_pressed['left'] and self.keys_pressed['right']:
            # Both pressed - decelerate to zero
            self.angle_velocity = 0
            if abs(self.angle) > 0.5:
                self.angle -= self.angle * self.decel_rate * dt / abs(self.angle)
            else:
                self.angle = 0
        else:
            # No keys - decelerate to zero
            self.angle_velocity = 0
            if abs(self.angle) > 0.5:
                decel_amount = self.decel_rate * dt
                if abs(self.angle) < decel_amount:
                    self.angle = 0
                else:
                    self.angle -= self.angle * decel_amount / abs(self.angle)
            else:
                self.angle = 0
        
        # Apply angle velocity
        if self.angle_velocity != 0:
            self.angle += self.angle_velocity * dt
            self.angle = max(self.angle_min, min(self.angle_max, self.angle))
        
        # ===== SPEED CONTROL =====
        if self.keys_pressed['up'] and not self.keys_pressed['down']:
            # Accelerate forward
            # If currently going backward, accelerate FASTER (reverse boost)
            if self.speed < 0:
                self.speed_velocity = self.accel_rate * 2.0  # 2x faster reverse!
            else:
                self.speed_velocity = self.accel_rate
        elif self.keys_pressed['down'] and not self.keys_pressed['up']:
            # Decelerate / reverse
            # If currently going forward, decelerate FASTER (reverse boost)
            if self.speed > 0:
                self.speed_velocity = -self.accel_rate * 2.0  # 2x faster reverse!
            else:
                self.speed_velocity = -self.accel_rate
        elif self.keys_pressed['up'] and self.keys_pressed['down']:
            # Both pressed - decelerate to zero
            self.speed_velocity = 0
            if abs(self.speed) > 0.5:
                self.speed -= self.speed * self.decel_rate * dt / abs(self.speed)
            else:
                self.speed = 0
        else:
            # No keys - decelerate to zero
            self.speed_velocity = 0
            if abs(self.speed) > 0.5:
                decel_amount = self.decel_rate * dt
                if abs(self.speed) < decel_amount:
                    self.speed = 0
                else:
                    self.speed -= self.speed * decel_amount / abs(self.speed)
            else:
                self.speed = 0
        
        # Apply speed velocity
        if self.speed_velocity != 0:
            self.speed += self.speed_velocity * dt
            self.speed = max(self.speed_min, min(self.speed_max, self.speed))
    
    def get_values(self):
        """Get current angle and speed (thread-safe)."""
        with self.lock:
            return self.angle, self.speed
    
    def reset(self):
        """Reset to zero."""
        with self.lock:
            self.angle = 0.0
            self.speed = 0.0
            self.angle_velocity = 0.0
            self.speed_velocity = 0.0


# Test
if __name__ == "__main__":
    import sys
    from pynput import keyboard
    
    controller = GamepadController()
    controller.start()
    
    def on_press(key):
        try:
            if key == keyboard.Key.left:
                controller.key_press('left')
            elif key == keyboard.Key.right:
                controller.key_press('right')
            elif key == keyboard.Key.up:
                controller.key_press('up')
            elif key == keyboard.Key.down:
                controller.key_press('down')
        except:
            pass
    
    def on_release(key):
        try:
            if key == keyboard.Key.left:
                controller.key_release('left')
            elif key == keyboard.Key.right:
                controller.key_release('right')
            elif key == keyboard.Key.up:
                controller.key_release('up')
            elif key == keyboard.Key.down:
                controller.key_release('down')
            elif key == keyboard.Key.esc:
                return False
        except:
            pass
    
    print("Test keyboard controller")
    print("Arrow keys to control, ESC to quit")
    print()
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    try:
        while listener.running:
            angle, speed = controller.get_values()
            print(f"\rAngle: {angle:7.2f}°  Speed: {speed:7.2f} RPM", end='')
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    
    controller.stop()
    print("\nTest complete!")
