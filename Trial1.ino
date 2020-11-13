

// define pins on the Arduino nano board. 
const int motor = 1; //Motor 1 or 2, still don't know exactly which one will move in which direction. 
const int leverPin = 9; //PWM pins on nano: 3, 9, 10, 11. 
const int stepPin = 3;  
const int dirPin = 2; 
const int switchPin = 6;

const int done = 999;
const int error = 666;

//Motor and lead screw specifics. 
const int pitch = 6; //Pitch in mm
const int RPM = 300; //Expected motor speed in rpm
const int wait = 1500; //(RPM*200)/(60*1000000). This sets the wait between output steps to the stepper motor. A longer wait will mean a slower motor speed. 

//Tray positions. 
static int new_pos;
static int cur_pos_case;
static int cur_pos_mm;

//---------------------------------------------------SETUP-----------------------------------------------------
void setup() {
  // Sets the two stepper motor pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  //Sets the lever pin as Output
  pinMode(leverPin,OUTPUT);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

//---------------------------------------------INITIATION/HOMING------------------------------------------------
void initiate(){
  
  analogWrite(leverPin, 19);
  
  //This continously runs the motor, one step at a time, untill the homing switch is reached. 
  int direction = 0;
  int steps = 1;
  
  while(1){
    stepperRun(direction,steps);
    if (digital.Read(switchPin) == HIGH){
      delay(50);
      break;
    }
  }
  cur_pos_mm = 0;
}

//----------------------------------------MOVE TRAY---------------------------------------------
void tray_drive(int position, prev_distance_mm){ 
  
  int position_mm = getDistance(position);
  int travel_mm = cur_pos_mm - (position_mm - prev_distance_mm);
  int steps = (travel_mm/pitch)*200;
  
  //Set direction. 
  if (steps < 0){
    digitalWrite(dirPin,HIGH);
  }
  else{
    digitalWrite(dirPin,LOW);
  } 
    
  // Makes 200 pulses for making one full rotation (1.8deg/step)
  int check = 0; 
  for(int x = 0; x < abs(steps); x++){
    
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    
    check++;
    //Writes to Rpi 10 times every rotation = every 0.6mm
    if (check%20 == 0{
      int mm = (check/200)*pitch;
      Serial.write(mm);
    }   
  }
  cur_pos_mm = position_mm;      
  delay(100); // 0.1 second delay
}

//-----------------------------------------MOVE LEVER---------------------------------------
void lever_drive(lever_command){
  
  int value; 
  switch (lever_command){
    case 1:
      value = 19;
      break;
    case 2:
      value = 17;
      break;
    case 3: 
      value = 21;
      break;
    case 4: 
      value = 13;
      break;
    case 5:
      value = 25;
      break;
  }

  analogWrite(leverPin, value);
  
}

//-------------------------------------GET DISTANCE IN MM------------------------------------
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

//------------------------------------------------MAIN------------------------------------------
void loop() {
  
  if (Serial.available()>0){
    
    int command = Serial.parseInt();
    Serial.read(); //there seems to be a "left over" 0 when using serial with the arduino app. This gets rid of it. 
    int state = command%1000000;
    
    //initiation command
    if (state == 0){  
      initiate(); 
      Serial.print(done);
    }
    
    //Position Query
    else if (state == 6){
      Serial.write(cur_pos_mm);
    }
    
    //Sensor query
    else if (state == 7){ 
      Serial.write("sensor");
    }
    
    //Lever change command
    else if (state == 8){  
      
      //Calculate commands
      int lever_command = command % 10;
      
      lever_drive(lever_command);
      Serial.write(done);
    }
    
    //Tray change command 
    else if (state == 0){ 
      
      //Calculate commands 
      int tray_command = (command % 1000000) / 10000;
      int distance_command = (command % 10000) / 10;
      
      tray_drive(tray_command, distance_command);
      Serial.write(done);
    }
    
    //ERROR
    else{
      Serial.write(error);
    }
    
  }
}
