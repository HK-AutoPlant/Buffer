// defines pins numbers
const int motor = 1; //left motor = 1, right motor = 2
const int stepPin = 3; 
const int dirPin = 2; 

const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000);

static int new_pos;
static int cur_pos_mm;

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
  
  cur_pos_mm = 0;
  Serial.print("Initiated.");
  Serial.println();
  Serial.println();
  
}

void drive(int new_pos){
  int steps; 
  steps = calc(new_pos);
  
  if (steps < 0){
    digitalWrite(dirPin,HIGH); // Enables the motor to move in a particular direction
    Serial.print("Setting direction to high.");
    Serial.println();
  }
  else{
    digitalWrite(dirPin,LOW);
    Serial.print("Setting direction to low.");
    Serial.println();
  }
    
  // Makes 200 pulses for making one full cycle rotation for 1.8deg/step motor
  int check = 0;
  Serial.print("Moving...");
  Serial.println();
  for(int x = 0; x < abs(steps); x++){
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait); 
    check++;
  }
  Serial.print(check);
  Serial.print(" steps completed");
  Serial.println();
  
  cur_pos_mm = getDistance(new_pos); 
  Serial.print("Current position: ");
  Serial.print(cur_pos_mm);
  Serial.println();
  delay(1000); // One second delay
}

int calc(int new_pos){
  int distance_mm, dir, steps, dist; 

  dist = getDistance(new_pos);
  Serial.print("Target distance from homing: ");
  Serial.print(dist);
  Serial.print(" [mm].");
  Serial.println();
  
  distance_mm = cur_pos_mm - dist; 
  Serial.print("Distance to travel: ");
  Serial.print(abs(distance_mm));
  Serial.print(" [mm].");
  Serial.println();
  
  steps = (distance_mm/6*200);
  Serial.print("Steps: ");
  Serial.print(abs(steps));
  Serial.println();
  
  return steps;
}

int getDistance(int new_pos){
  int dist;

  switch (new_pos){
    case 1:
      dist = 405; //405.25
      break;
    case 11:
      dist = 5;
      break;
    case 12:
      dist = 75; //75.2
      break;
    case 21:
      dist = 75; //75.2
      break;
    case 13:
      dist = 145; //145.4
      break;
    case 22:
      dist = 145; //145.4
      break;
    case 14:
      dist = 216; //215.6
      break;
    case 23:
      dist = 216; //215.6
      break;
    case 15:
      dist = 286; //285.8
      break;
    case 24:
      dist = 286; //285.8
      break;
    case 25:
      dist = 356;
      break;
  }
  return dist;
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
  Serial.read();
  Serial.print("New position demand detected:");
  Serial.println();
  Serial.print(new_pos);
  Serial.println();
  new_pos = new_pos%100;
  if (new_pos == 0){
    ining = 1; 
    Serial.print("Initiating again.");
    Serial.println();
  }
  else{
    Serial.print("Moving to: ");
    Serial.print(new_pos);
    Serial.println();
    drive(new_pos);
  }
  }
}
}
