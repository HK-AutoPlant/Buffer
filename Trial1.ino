// defines pins numbers
const int motor = 1; //left motor = 1, right motor = 2
const int stepPin = 3; 
const int dirPin = 2; 

const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000);

static int new_pos;
static int cur_pos;

void setup() {
  // Sets the two pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

void initiate(){
  delay(1000);
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
  delay(1000);
  
  cur_pos = 0;
  Serial.print("Initiated.");
  Serial.println();
  
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
  delay(1000);
  Serial.print("Welcome!");
  Serial.println();
  initiate();
  int ining = 0;
  while(ining == 0){
  if (Serial.available()>0){
  new_pos = Serial.parseInt();
  Serial.print("New position demand detected.");
  Serial.print(new_pos);
  Serial.println();
  new_pos = new_pos%100;
  if (new_pos == 0){
    ining = 1; 
    Serial.print("Initiating again.");
    Serial.println();
  }
  else{
    drive(new_pos);
  }
  }
}
}
