

// define pins on the Arduino nano board. 
const int motor = 1; //Motor 1 or 2, still don't know exactly which one will move in which direction. 
const int stepPin = 3;  
const int dirPin = 2; 

//Motor and lead screw specifics. 
const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000). This sets the wait between output steps to the stepper motor. A longer wait will mean a slower motor speed. 

//Tray positions. 
static int new_pos;
static int cur_pos_mm;

//---------------------------------------------------SETUP-----------------------------------------------------
void setup() {
  // Sets the two pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

//---------------------------------------------INITIATION/HOMING------------------------------------------------
void initiate(){
  delay(1000);
  
  //Setting direction depending on which tray the arduino is controlling. The motors/trays are not yet defined. 
  if (motor == 1){
    digitalWrite(dirPin,HIGH);
    }
  if (motor == 2){
    digitalWrite(dirPin,LOW);
    }
    
  //This continously runs the motor untill the homing switch is reached. 
  for(int x = 0; x < 100; x++){//while(no signal from switch){
    digitalWrite(stepPin,HIGH);
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    }
  delay(1000);
  
  //Update the tray position to the homing position = 0mm. 
  cur_pos_mm = 0;
  
  //Send clear signal to the Raspberry Pi = 999. 
  Serial.print("999");
}

//----------------------------------------DRIVE TO REQUIRED POSITION---------------------------------------------
void drive(int new_pos){
  int steps; 
  
  //Calls the calc() function which returns the steps and direction (+/-) required to move to the new position.
  steps = calc(new_pos);
  
  //Sets direction of motor depending on the result from the calc() function (+/-) and the operating motor. 
  if (steps < 0){
    if (motor == 1){
      digitalWrite(dirPin,HIGH);
    }
    else{
      digitalWrite(dirPin,LOW);
    } 
  }
  else{
    if (motor == 1){
      digitalWrite(dirPin,LOW);
    }
    else{
      digitalWrite(dirPin,HIGH);
    }
  }
    
  // Makes 200 pulses for making one full rotation (1.8deg/step)
  int check = 0; 
  for(int x = 0; x < abs(steps); x++){
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    check++;
    }
  }
  
  //Update the position in mm of the tray using the getDistance() function. 
  cur_pos_mm = getDistance(new_pos); 

  delay(1000); // One second delay
  
  //Return the clear signal to the Raspberry Pi, move is completed! 
  Serial.print("999");
}

//---------------------------------------CALCULATE DISTANCE TO WANTED POSITION--------------------------------
int calc(int new_pos){
  int distance_mm, dir, steps, dist; 

  //Use the getDistance() function to calculate the wanted distance from homing. 
  dist = getDistance(new_pos);
  
  //Calculate distance and steps to move from current position. 
  distance_mm = cur_pos_mm - dist; 
  steps = (distance_mm/6*200);
  
  //Return steps (positive and negative value indicate the direction)
  return steps;
}

//---------------------------------------------
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
