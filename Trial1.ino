#include <Servo.h>
Servo lever;

// define pins on the Arduino nano board. 
const int motor = 1; //Motor 1 or 2 
const int leverPin = 9; //PWM pins on nano: 3, 9, 10, 11. 
const int stepPin = 3;  
const int dirPin = 2; 
const int switchPin = 7;

int lever_drive(int);
int getDistance(int);
int tray_drive(int, int);

const int done = 999;
const int error = 666;
const int travel_limit_mm = 372;

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
  pinMode(switchPin,INPUT);
  //Sets the lever pin as Output
  lever.attach(leverPin);
  // Sets up usb connection to Raspberry Pi 
  Serial.begin(9600);
}

//---------------------------------------------INITIATION/HOMING------------------------------------------------
void initiate(){
  
  lever.write(95);
  
  //This continously runs the motor, one step at a time, untill the homing switch is reached. 
  digitalWrite(dirPin,LOW);
  
  while(1){
    digitalWrite(stepPin,HIGH); 
    delayMicroseconds(wait); 
    digitalWrite(stepPin,LOW); 
    delayMicroseconds(wait);
    if (digitalRead(switchPin) == HIGH){
      delay(50);
      delay(1000);
      break;
    }
  }
  cur_pos_mm = 0;
}

//----------------------------------------MOVE TRAY---------------------------------------------
int tray_drive(int position, int prev_distance_mm){ 

  int travel_mm, steg, fatal = 0;
  
  int position_mm = getDistance(position);
  if (position_mm > travel_limit_mm){
      fatal = 1;
    }
  
  travel_mm = position_mm - (cur_pos_mm - prev_distance_mm);
  if (abs(travel_mm + cur_pos_mm) < travel_limit_mm){   
    
    steg = (travel_mm)*33.33333;

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

      if (switchPin == HIGH){
        fatal = 1;
        break;
      }
    
      check++;
      //Writes to Rpi 10 times every rotation = every 0.6mm
      if (check == 20){
        check = 0; 
      } 
    }
    
    if (fatal == 0){
      cur_pos_mm = position_mm;}    
    delay(100); // 0.1 second delay
  }
  
  else{
    fatal = 1
  }
  return fatal;
}

//-----------------------------------------MOVE LEVER---------------------------------------
int lever_drive(int lever_command){
  
  int value = 400; 
  int fatal = 0;
  
  switch (lever_command){
    case 0:
      value = 95;
      break;
    case 1:
      if (motor == 1){
        value = 30}
      else{
        value = 170}
      break;
  }

  if (value == 400){
    fatal = 1}
  else{
    lever.write(value);}
  
  return fatal;
  
}

//-------------------------------------GET DISTANCE IN MM------------------------------------
int getDistance(int new_pos){
  int dist = 400;

  switch (new_pos){
    case 0:
      dist = 0;
      break;
    case 6:
      dist = 371; //405.25
      break;
    case 1:
      dist = 5;
      break;
    case 2:
      dist = 75; //75.2
      break;
    case 3:
      dist = 145; //145.4
      break;
    case 4:
      dist = 216; //215.6
      break;
    case 5:
      dist = 286; //285.8
      break;
  }
  return dist;
}

//------------------------------------------------MAIN------------------------------------------
void loop() {

  String str_command;
  long int_command;
  
  if (Serial.available()>0){
  
    str_command = Serial.readStringUntil("/r");
    int_command = str_command.toInt();
    
    //OLD COMMANDS 
    //int state = int_command/1000000;
    //int tray_command = (int_command % 1000000) / 10000;
    //int distance_command = (int_command % 10000) / 10;
    //int lever_command = int_command % 10;
    
    int arduino = int_command / 1000000;
    int state = (int_command % 1000000) / 100000;
    int tray_command = (int_command % 100000) / 10000;
    int distance_command = (int_command % 10000) / 10;
    int lever_command = int_command % 10;
    
    if (arduino == motor){
      
    //initiation command
    if (state == 0){ 
      initiate(); 
      Serial.write(done);
    }
    
    //Position Query
    else if (state == 6){
      Serial.write(cur_pos_mm);
    }
    
    //Sensor query
    else if (state == 7){ 
      Serial.write("Query: sensor");
    }
    
    //Lever change command
    else if (state == 8){  
      
      if (lever_drive(lever_command) == 1){
        Serial.write(error);}
      else {
        Serial.write(done);}
    }
    
    //Tray change command 
    else if (state == 1){ 
      if(tray_drive(tray_command, distance_command) == 1){
        Serial.write(error);}
      else{
        Serial.write(new_pos_mm)}
    }
    
    //ERROR
    else{
      Serial.write(error);
    }
    }
    
  }
}
