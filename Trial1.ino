// defines pins numbers
const int stepPin = 3; 
const int dirPin = 4; 
const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000);

const int travel = 100; //Travel in mm
const int steps = (travel/6)*200;
void setup() {
  // Sets the two pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
}
void loop() {
  digitalWrite(dirPin,HIGH); // Enables the motor to move in a particular direction
  // Makes 200 pulses for making one full cycle rotation for 1.8deg/step motor
  for(int x = 0; x < steps; x++) {
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait); 
  }
  delay(1000); // One second delay
  
  digitalWrite(dirPin,LOW); //Changes the rotations direction
  // Makes 400 pulses for making two full cycle rotation
  for(int x = 0; x < steps; x++) {
    digitalWrite(stepPin,HIGH);
    delayMicroseconds(wait);
    digitalWrite(stepPin,LOW);
    delayMicroseconds(wait);
  }
  delay(1000);
}
