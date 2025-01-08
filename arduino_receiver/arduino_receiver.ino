#include <SPI.h>
#include <RF24.h> // Library for controlling WS2812 or similar LEDs
#include <Adafruit_NeoPixel.h>  // Library for controlling WS2812 or similar LEDs

// nRF24L01 -> Arduino wiring:
// GND  -> GND
// CE   -> D10
// SCK  -> D13
// MISO -> D12
// VCC  -> 3.3V (DO NOT USE 5V !!!) 
// CSN  -> D9
// MOSI -> D11


// "left": ID=1
// "top": ID=2
// "right": ID=3
// "bottom": ID=4
// "full_screen": ID=5
#define ID 1  // Fixed ID of this node, this controls which border of the screen its colors it will use

// IMPORTANT! Check the config.ini on the Raspberry!
// COLORS_IN_PAYLOAD MUST MATCH RASPBERRY config.ini  = how much colors the raspberry will broadcast in each payload
// default = 10
#define COLORS_IN_PAYLOAD 10 

// COLOR_COUNT MUST MATCH RASPBERRY config.ini = how much colors the raspberry will send out for each specific ID (possibly over multiple payloads)
// for ID = 1 (left) or 3 (right) this must be the same as VERTICAL_LEDS in config.ini -> default = 10
// for ID = 2 (top) or 4 (down) this must be the same as HORIZONTAL_LEDS in config.ini -> default = 10
// for id = 5 (full_screen) this must be: 1 -> only 1 is allowed for ID 5
#define COLOR_COUNT 10 

// Brightness of the LED strip (0: dimmed to 255: brightest)
#define BRIGHTNESS 255

#define LED_PIN 6  // Digital IO pin connected to the LED strip. Don't forget to add 330 Ohm resistor
#define LED_COUNT 10  // Number of LEDs in your LED strip, change to your needs
const bool strip_orientation = true; // use false or true to change orientation
const float transitionSpeed = 0.1; // transition speed between different colours (best between 0.1 - 1)

unsigned long lastActivityTime = 0; // Time of last button received payload
const unsigned long timeout = 30 * 1000; // x milliseconds timeout (turn off after duration no colors were received)

// Don't change this
#define INT_COUNT 2 + 3 * COLORS_IN_PAYLOAD  // ID + OFFSET + 3*COLORS

// nRF24L01 pins: CE -> D10, CSN -> D9
RF24 radio(10, 9);

// Declare our NeoPixel strip object:
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
// Argument 1 = Number of pixels in NeoPixel strip
// Argument 2 = Arduino pin number (most are valid)
// Argument 3 = Pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
//   NEO_RGBW    Pixels are wired for RGBW bitstream (NeoPixel RGBW products)


struct payload_t {
  uint8_t data[INT_COUNT];
};

struct Color {
  uint8_t r, g, b;
};

Color currentColors[COLOR_COUNT];

void setup() {
  strip.begin();
  strip.show();  // Turn off all pixels
  strip.setBrightness(BRIGHTNESS);

  while (!Serial) {
    // Wait for serial if needed
  }

  if (!radio.begin()) {
    while (1) {
      for (int i = 0; i < 5; i++) {
        strip.setPixelColor(i, strip.Color(255, 255, 0));  // Flicker yellow to indicate arduino can't connect to nrf24L01 module
      }
      strip.show();
      delay(500);
      strip.clear();
      strip.show();
      delay(500);
    }
  }

  // Blink green to indicate potential succesfully connected to nrf24L01 module: there could still be a miswiring but a part of the cables is at least connected correctly
  for (int i = 0; i < 5; i++) {
    strip.setPixelColor(i, strip.Color(0, 255, 0));  // Green for success
  }
  strip.show();
  delay(1000);
  strip.clear();
  strip.show();

  // Configure the radio
  radio.setDataRate(RF24_2MBPS);  // Match data rate with transmitter
  radio.setChannel(90);          // Match channel with transmitter
  radio.openReadingPipe(1, 0xF0F0F0F0E1);  // Match address with transmitter
  radio.setAutoAck(false);       // Disable AutoAck to broadcast payloads without waiting for confirmation
  radio.startListening();        // Start listening for packets

  // Initialize current colors to off
  for (int i = 0; i < COLOR_COUNT; i++) {
    currentColors[i] = {0, 0, 0};
  }
  lastActivityTime = millis(); // Update last activity time
}

Color transitionColor(Color current, Color target, float step) {
  current.r += (target.r - current.r) * step;
  current.g += (target.g - current.g) * step;
  current.b += (target.b - current.b) * step;
  return current;
}

void handleData(){
  payload_t payload;
  radio.read(&payload, sizeof(payload));  // Read the incoming data

  int id = payload.data[0];  // First byte is the ID
  if (id != ID) {
    return;  // Ignore updating LED lights if ID doesn't match
  }
  lastActivityTime = millis(); // Update last activity time

  int offset = payload.data[1];  // Second byte is the offset
  int rgb[INT_COUNT - 2];  // Array for RGB values
  for (int i = 0; i < INT_COUNT - 2; i++) {
    rgb[i] = payload.data[i + 2];
  }

  // Update LEDs with received colors
  // Taking offset into account when multiple payloads are expected for the same ID (default not the case)
  for (int i = 0; i < COLORS_IN_PAYLOAD; i++) {
    if (i + offset >= COLOR_COUNT) {
      continue;
    }
    uint8_t b = rgb[i * 3];
    uint8_t g = rgb[i * 3 + 1];
    uint8_t r = rgb[i * 3 + 2];

    int index = strip_orientation ? i + offset : COLOR_COUNT - 1 - (i + offset);
    currentColors[index] = {r, g, b};
  }
}

void loop() {
  static unsigned long lastUpdate = 0;

  unsigned long now = millis();
  if (now - lastUpdate > 15) { // Adjust refresh rate (ms), this small delay is desired for optimal performance
    lastUpdate = now;

    for (int i = 0; i < LED_COUNT; i++) {
      if (radio.available()) handleData(); // First handle data if there is any available
      Color target = {0,0,0};
      if (millis() - lastActivityTime > timeout) { // After certain time of no payloads, turn off lights
        target = {0,0,0};
      }
      else{

        // Following lines of code will spread out the smaller number of received lights (example for ID 1 default 10 colours will be broadcasted)
        // Spread out the limited amount of lights in the payload over the larger amount (or smaller) of actual LED lights on the strip
        // When spreading out over larger amount of LED lights, this smooths out the effect and looks nicer (that's why default is not larger than 10 per payload)
        float ratio = (float)i / (LED_COUNT - 1); // Calculate the position ratio
        float scaledIndex = ratio * (COLOR_COUNT - 1); // Map to fixed color indices
        int indexLow = floor(scaledIndex);
        int indexHigh = ceil(scaledIndex);
        float blendFactor = scaledIndex - indexLow; // Distance from the lower index

        // Get the low and high fixed colors next to our current LED light
        Color colorLow = currentColors[indexLow];
        Color colorHigh = currentColors[indexHigh];

        // Blend the two colors
        target = {
          (1 - blendFactor) * colorLow.r + blendFactor * colorHigh.r,
          (1 - blendFactor) * colorLow.g + blendFactor * colorHigh.g,
          (1 - blendFactor) * colorLow.b + blendFactor * colorHigh.b
        };
      }

      // Get the current color of the LED
      Color current = {
        strip.getPixelColor(i) >> 16 & 0xFF,
        strip.getPixelColor(i) >> 8 & 0xFF,
        strip.getPixelColor(i) & 0xFF
      };
      // Transition to the target color
      Color newColor = transitionColor(current, target, transitionSpeed);

      // Set the LED to the new color
      strip.setPixelColor(i, strip.Color(newColor.r, newColor.g, newColor.b));
    }
    strip.show(); // Update all updated LED lights after the for-loop
  }
}
