/*********************************************************************
 This is an example for our nRF52 based Bluefruit LE modules

 Pick one up today in the adafruit shop!

 Adafruit invests time and resources providing this open source code,
 please support Adafruit and open-source hardware by purchasing
 products from Adafruit!

 MIT license, check LICENSE for more information
 All text above, and the splash screen below must be included in
 any redistribution
*********************************************************************/
#include <bluefruit.h>

BLEHidAdafruit blehid;

void setup() {
  Serial.begin(115200);

  Bluefruit.begin();
  Bluefruit.setTxPower(4);  // Check bluefruit.h for supported values
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);
  Bluefruit.Periph.setConnectCallback(connect_callback);
  Bluefruit.Periph.setConnInterval(6, 12);  // 7.5 - 15 ms

  /* Start BLE HID
   * Note: Apple requires BLE device must have min connection interval >= 20m
   * ( The smaller the connection interval the faster we could send data).
   * However for HID and MIDI device, Apple could accept min connection interval 
   * up to 11.25 ms. Therefore BLEHidAdafruit::begin() will try to set the min and max
   * connection interval to 11.25  ms and 15 ms respectively for best performance.
   */
  blehid.begin();

  // Set callback for set LED from central
  blehid.setKeyboardLedCallback(set_keyboard_led);

  /* Set connection interval (min, max) to your perferred value.
   * Note: It is already set by BLEHidAdafruit::begin() to 11.25ms - 15ms
   * min = 9*1.25=11.25 ms, max = 12*1.25= 15 ms 
   */
  /* Bluefruit.Periph.setConnInterval(9, 12); */

  // Set up and start advertising
  startAdv();
}

void startAdv(void) {
  // Advertising packet
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addAppearance(BLE_APPEARANCE_HID_KEYBOARD);
  Bluefruit.Advertising.addAppearance(BLE_APPEARANCE_HID_MOUSE);

  // Include BLE HID service
  Bluefruit.Advertising.addService(blehid);

  // There is enough room for the dev name in the advertising packet
  Bluefruit.Advertising.addName();

  /* Start Advertising
   * - Enable auto advertising if disconnected
   * - Interval:  fast mode = 20 ms, slow mode = 152.5 ms
   * - Timeout for fast mode is 30 seconds
   * - Start(timeout) with timeout = 0 will advertise forever (until connected)
   * 
   * For recommended advertising interval
   * https://developer.apple.com/library/content/qa/qa1931/_index.html   
   */
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);  // in unit of 0.625 ms
  Bluefruit.Advertising.setFastTimeout(30);    // number of seconds in fast mode
  Bluefruit.Advertising.start(0);              // 0 = Don't stop advertising after n seconds
}

void connect_callback(uint16_t conn_handle) {
}

void loop() {

  delay(1);

  while (Serial.available() >= 8) {
    uint8_t type = Serial.read();
    if (type == 0xbd) {
      uint8_t current_modifier = Serial.read();
#define KEYCODE_NUM 6
      uint8_t current_keycode[KEYCODE_NUM];
      for (int i = 0; i < KEYCODE_NUM; i++) {
        current_keycode[i] = Serial.read();
      }
      blehid.keyboardReport(current_modifier, current_keycode);
    } else if (type == 0x5e) {
      uint8_t mouse_buttons = Serial.read();
      int8_t mouse_x = Serial.read();
      int8_t mouse_y = Serial.read();
      int8_t mouse_wheel = Serial.read();
      uint8_t dammy1 = Serial.read();
      uint8_t dammy2 = Serial.read();
      uint8_t dammy3 = Serial.read();
      blehid.mouseReport(mouse_buttons, mouse_x, mouse_y, mouse_wheel);
    }
  }
}

/**
 * Callback invoked when received Set LED from central.
 * Must be set previously with setKeyboardLedCallback()
 *
 * The LED bit map is as follows: (also defined by KEYBOARD_LED_* )
 *    Kana (4) | Compose (3) | ScrollLock (2) | CapsLock (1) | Numlock (0)
 */
void set_keyboard_led(uint16_t conn_handle, uint8_t led_bitmap) {
  (void)conn_handle;

  // light up Red Led if any bits is set
  if (led_bitmap) {
    ledOn(LED_RED);
  } else {
    ledOff(LED_RED);
  }
}
