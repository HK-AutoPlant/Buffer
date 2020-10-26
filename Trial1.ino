
/*
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

*/
// defines pins numbers
const int motor = 1; //left motor = 1, right motor = 2
const int stepPin = 3; 
const int dirPin = 2; 

const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000);

static int new_pos;
static int cur_pos; 

const int homing = 0;
const int refill = 800; 
const int c1 = 740;
const int c2 = 700;
const int d1 = 700; 
const int c3 = 650;
const int d2 = 650;
const int c4 = 550;
const int d3 = 550;
const int c5 = 450;
const int d4 = 450;
const int d5 = 350; 

void setup() {
  // Sets the two pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

void initiate(){
  delay(5000);
  if (motor == 1){
    digitalWrite(dirPin,HIGH);
    }
  if (motor == 2){
    digitalWrite(dirPin,LOW);
    }
    
  for(int x = 0; x < 100; x++){//while(no signal from switch){
    digitalWrite(stepPin,HIGH);
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    }
  delay(5000);
  
  cur_pos = homing; 
  
}

void drive(int new_pos){
  int steps, dir; 
  steps, dir = calc(new_pos);
  if (dir == 0){
    digitalWrite(dirPin,HIGH); // Enables the motor to move in a particular direction
  }
  else{
    digitalWrite(dirPin,LOW);
  }
    
  // Makes 200 pulses for making one full cycle rotation for 1.8deg/step motor
  for(int x = 0; x < steps; x++){
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait); 
  }
  
  cur_pos = new_pos; 
  delay(1000); // One second delay
}

int calc(int new_pos){
  int distance_mm, dir, steps; 
  
  distance_mm = cur_pos - new_pos; 
  if (distance_mm > 0) {
    dir = 1;
  }
  else{
    dir = 0;
  }
  
  steps = (distance_mm/6*200);
  
  return steps, dir;
}

void loop() {
  initiate();
  while(1){
  while (Serial.available()==0){
  }
  new_pos = Serial.read();
  if (new_pos == 100 or new_pos == 200){
    //break while loop and initiate again. 
  }
  else{
    drive(new_pos);
  }
  }
}
