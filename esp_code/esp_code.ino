#include <WiFi.h>
#include <ESPAsyncWebServer.h>

#define ENA 32
#define ENB 14
#define IN1 33
#define IN2 25
#define IN3 26
#define IN4 27

const char* ssid = "OnePlus 9 Pro 5G";
const char* password = "karim2003";

int y = 0;
int yaw = 0;

int motor_left = 0;
int motor_right = 0;

int curr_motor_left = 0;
int curr_motor_right = 0;

float alpha = 0.9;

AsyncWebServer server(8080);

// Static IP configuration
IPAddress local_IP(192, 168, 115, 125); // Set your desired static IP
IPAddress gateway(192, 168, 1, 105);   // Typically your router's IP
IPAddress subnet(255, 255, 255, 0);  // Subnet mask

void setup() {
  Serial.begin(115200);
  
  // Configure static IP
  if (!WiFi.config(local_IP, gateway, subnet)) {
    Serial.println("STA Failed to configure");
  }
  
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());

  // POST endpoint to receive two integers
  server.on("/speeds", HTTP_POST, [](AsyncWebServerRequest *request) {
    String y_str = "";
    String yaw_str = "";

    // Check and retrieve the values of "y" and "yaw"
    if (request->hasParam("y", true)) {
      y_str = request->getParam("y", true)->value();
    }
    if (request->hasParam("yaw", true)) {
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
    request->send(200, "text/plain", "Speeds Received and Processed " + String(curr_motor_left) + "," + String(curr_motor_right));

  });

  server.begin();

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
}

void loop() {
    motor_left = (y - yaw)*-1;
    motor_right = y + yaw;

    int max_s = max(abs(motor_left), abs(motor_right));

    if (max_s > 255) {
      motor_left *= 255 / max_s;
      motor_right *= 255 / max_s;
    }

    curr_motor_left = curr_motor_left * alpha + motor_left * (1 - alpha);
    curr_motor_right = curr_motor_right * alpha + motor_right * (1 - alpha);

    if(curr_motor_left>0){
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    }
    else{
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
    }
    analogWrite(ENA, abs(curr_motor_left));
  
    if(curr_motor_right>0){
      digitalWrite(IN3, LOW);
      digitalWrite(IN4, HIGH);
    }
    else{
      digitalWrite(IN3, HIGH);
      digitalWrite(IN4, LOW);
    }
    analogWrite(ENB, abs(curr_motor_right));
  
    Serial.println(curr_motor_left);
    Serial.println(curr_motor_right);
delay(7);

    
}
