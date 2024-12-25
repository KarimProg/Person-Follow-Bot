#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

#define ENA 32
#define ENB 14
#define IN1 33
#define IN2 13
#define IN3 26
#define IN4 27

const char *ssid = "HOTTT";
const char *password = "karim1511";

int y = 0;
int yaw = 0;

int motor_left = 0;
int motor_right = 0;

int curr_motor_left = 0;
int curr_motor_right = 0;

float alpha = 0.9;

AsyncWebServer server(8080);

// Static IP configuration
IPAddress local_IP(10, 42, 0, 253); // Set your desired static IP
IPAddress gateway(10, 42, 0, 1);    // Typically your router's IP
IPAddress subnet(255, 255, 255, 0); // Subnet mask

// Define PWM properties
const int freq = 5000;
const int ledChannel1 = 0;
const int ledChannel2 = 1;
const int resolution = 8;

void handleWiFi(void *parameter)
{
    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    if (!WiFi.config(local_IP, gateway, subnet))
    {
        Serial.println("STA Failed to configure");
    }
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    // Start server
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request)
              { request->send(200, "text/plain", "Hello, world"); });

    server.on("/speeds", HTTP_POST, [](AsyncWebServerRequest *request)
              {
        String y_str;
        String yaw_str;

        if (request->hasParam("y", true))
        {
            y_str = request->getParam("y", true)->value();
        }
        if (request->hasParam("yaw", true))
        {
            yaw_str = request->getParam("yaw", true)->value();
        }

        // Convert received strings to integers
        y = y_str.toInt();
        yaw = yaw_str.toInt();

        // Log the received values and the result
        Serial.println("Received Integers:");
        Serial.println("y: " + y_str);
        Serial.println("yaw: " + yaw_str);

        // Respond to the client
        request->send(200, "text/plain", "Speeds Received and Processed " + String(curr_motor_left) + "," + String(curr_motor_right)); });

    server.begin();

    for (;;)
    {
        // Handle WiFi tasks
        delay(50);
    }
}

void handleMotors(void *parameter)
{
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);

    for (;;)
    {
        motor_left = (y - yaw) * -1;
        motor_right = y + yaw;

        int max_s = max(abs(motor_left), abs(motor_right));

        if (max_s > 255)
        {
            motor_left = motor_left * 255 / max_s;
            motor_right = motor_right * 255 / max_s;
        }

        curr_motor_left = alpha * curr_motor_left + (1 - alpha) * motor_left;
        curr_motor_right = alpha * curr_motor_right + (1 - alpha) * motor_right;

        ledcWrite(ENA, abs(curr_motor_left));
        ledcWrite(ENB, abs(curr_motor_right));

        digitalWrite(IN1, curr_motor_left > 0);
        digitalWrite(IN2, curr_motor_left < 0);
        digitalWrite(IN3, curr_motor_right > 0);
        digitalWrite(IN4, curr_motor_right < 0);

        delay(10); // Adjust the delay as needed
    }
}

void setup()
{
    Serial.begin(115200);
    ledcAttachChannel(ENA, freq, resolution, ledChannel1);
    ledcAttachChannel(ENB, freq, resolution, ledChannel2);

    // Create tasks and pin them to specific cores
    xTaskCreatePinnedToCore(
        handleWiFi, // Task function
        "WiFiTask", // Name of the task
        10000,      // Stack size
        NULL,       // Task input parameter
        1,          // Priority of the task
        NULL,       // Task handle
        0);         // Core to run the task on (0 or 1)

    xTaskCreatePinnedToCore(
        handleMotors, // Task function
        "MotorTask",  // Name of the task
        10000,        // Stack size
        NULL,         // Task input parameter
        1,            // Priority of the task
        NULL,         // Task handle
        1);           // Core to run the task on (0 or 1)
}

void loop()
{
    // The loop function can remain empty if all tasks are handled by the created tasks
}
