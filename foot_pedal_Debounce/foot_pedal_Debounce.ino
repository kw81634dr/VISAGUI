/*

  Debounce buttons and trigger events
  Copyright (C) 2015-2018 by Xose Pérez <xose dot perez at gmail dot com>

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

#include <Arduino.h>
#include "Keyboard.h"
#include <DebounceEvent.h>

#define BUTTON_PIN              2

#define CUSTOM_DEBOUNCE_DELAY   50

// Time the library waits for a second (or more) clicks
// Set to 0 to disable double clicks but get a faster response
#define CUSTOM_REPEAT_DELAY     500

DebounceEvent * button;

byte is_needSerial = 0;
byte is_send_key = 1;

void setup() {
  if (is_needSerial) Serial.begin(115200);
  if (is_needSerial) Serial.println();
  if (is_needSerial) Serial.println();
  button = new DebounceEvent(BUTTON_PIN, BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP, CUSTOM_DEBOUNCE_DELAY, CUSTOM_REPEAT_DELAY);
}

// Available Event:EVENT_NONE, EVENT_CHANGED, EVENT_PRESSED,EVENT_RELEASED

void loop() {
  if (unsigned int event = button->loop()) {
    if (event == EVENT_RELEASED) {
      byte count = button->getEventCount();
      unsigned int duration = button->getEventLength();
      if (is_needSerial) Serial.print("Count : "); Serial.print(count);
      if (is_needSerial) Serial.print(" Length: "); Serial.print(duration);
      if (is_needSerial) Serial.println();
      if (duration > CUSTOM_REPEAT_DELAY) {
        send_clearall_key();
      } else {
        switch (count) {
          case 1:
            send_runstop_key();
            break;

          case 2:
            send_scrshot_key();
            break;
        }

      }

    }
  }
}

void send_runstop_key(void) {
  if (is_send_key) Keyboard.press(KEY_RIGHT_CTRL);
  delay(50);
  if (is_send_key) Keyboard.press(KEY_RETURN);
  if (is_needSerial)Serial.println("<RIGHT_CTRL>+<Return> Key");
  delay(50);
  if (is_send_key) Keyboard.releaseAll();
  if (is_needSerial) Serial.println("Release");
}

void send_scrshot_key(void) {
  if (is_send_key) Keyboard.write(KEY_RETURN);
  delay(10);
  if (is_needSerial) Serial.println("Return Key");
}

void send_clearall_key(void) {
  if (is_send_key) Keyboard.press(KEY_RIGHT_CTRL);
  delay(50);
  if (is_send_key) Keyboard.press(KEY_DELETE);
  if (is_needSerial) Serial.println("<RIGHT_CTRL>+<Delete> Key");
  delay(50);
  if (is_send_key) Keyboard.releaseAll();
  if (is_needSerial) Serial.println("Release");
}
