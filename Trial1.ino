#include <Servo.h>
Servo lever;

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
const int wait = 550; //(RPM*200)/(60*1000000). This sets the wait between output steps to the stepper motor. A longer wait will mean a slower motor speed. 

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
  lever.attach(leverPin);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

//---------------------------------------------INITIATION/HOMING------------------------------------------------
void initiate(){
  
  analogWrite(leverPin, 19);
  
  //This continously runs the motor, one step at a time, untill the homing switch is reached. 
  digitalWrite(dirPin,LOW);
  
  while(1){
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    if (digitalRead(switchPin) == HIGH){
      delay(50);
      break;
    }
  }
  cur_pos_mm = 0;
}

//----------------------------------------MOVE TRAY---------------------------------------------
void tray_drive(int position, int prev_distance_mm){ 
  
  int position_mm = getDistance(position);
  Serial.println(position_mm);
  int travel_mm = position_mm - (cur_pos_mm - prev_distance_mm);
  Serial.println(travel_mm);
  int steg = ((travel_mm)*200)/pitch;
  Serial.println(steg);
  
  //Set direction. 
  if (travel_mm > 0){
    digitalWrite(dirPin,HIGH);
  }
  else{
    digitalWrite(dirPin,LOW);
  } 
    
  // Makes 200 pulses for making one full rotation (1.8deg/step)
  int check = 0; 
  for(int x = 0; x < abs(steg); x++){
    
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    
    check++;
    //Writes to Rpi 10 times every rotation = every 0.6mm
    if (check%20 == 0){
      long int mm = (check*6)/200;
    }   
  }
  cur_pos_mm = position_mm;
  Serial.println("Current position: ");
  Serial.println(cur_pos_mm);      
  delay(100); // 0.1 second delay
}

//-----------------------------------------MOVE LEVER---------------------------------------
void lever_drive(int lever_command){
  
  int value; 
  switch (lever_command){
    case 1:
      value = 95;
      break;
    case 2:
      value = 60;
      break;
    case 3: 
      value = 135;
      break;
    case 4: 
      value = 30;
      break;
    case 5:
      value = 170;
      break;
  }

  lever.write(value);
  
}

//-------------------------------------GET DISTANCE IN MM------------------------------------
int getDistance(int new_pos){
  int dist;

  switch (new_pos){
    case 0:
      dist = 0;
      break;
    case 1:
      dist = 371; //405.25
      break;
    case 11:
      dist = 5;
      break;
    case 12:
      dist = 75; //75.2
      break;
    case 13:
      dist = 145; //145.4
      break;
    case 14:
      dist = 216; //215.6
      break;
    case 15:
      dist = 286; //285.8
      break;
    case 25:
      dist = 350;
      break;
  }
  return dist;
}

//------------------------------------------------MAIN------------------------------------------
void loop() {

  String str_command;
  long int_command;
  
  if (Serial.available()>0){
    
    Serial.println("command received:");
    str_command = Serial.readStringUntil("/r");
    Serial.println(str_command);
    int_command = str_command.toInt();

    int state = int_command/1000000;
    int tray_command = (int_command % 1000000) / 10000;
    int distance_command = (int_command % 10000) / 10;
    int lever_command = int_command % 10;
    
    //initiation command
    if (state == 0){  
      //initiate(); 
      Serial.print("done");
    }
    
    //Position Query
    else if (state == 6){
      Serial.write("Query: cur_pos_mm");
    }
    
    //Sensor query
    else if (state == 7){ 
      Serial.write("Query: sensor");
    }
    
    //Lever change command
    else if (state == 8){  
      
      lever_drive(lever_command);
      Serial.write("Servo, done");
    }
    
    //Tray change command 
    else if (state == 1){ 

      Serial.println("Moving tray!");
      tray_drive(tray_command, distance_command);
      Serial.write("Tray, done");
    }
    
    //ERROR
    else{
      Serial.write(error);
    }
    
  }
}
