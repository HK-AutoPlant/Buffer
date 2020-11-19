#include <Servo.h>
Servo lever;

// define pins on the Arduino nano board. 
const int motor = 1; //Motor 1 or 2, still don't know exactly which one will move in which direction. 
const int leverPin = 9; //PWM pins on nano: 3, 9, 10, 11. 
const int stepPin = 3;  
const int dirPin = 2; 
const int switchPin = 7;

int tray_drive(int, int);
int lever_drive(int);
int getDistance(int);

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
static bool lever_up;

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
  lever_up = false;
  
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

int travel_mm, steg;
int fatal = 0;

if (lever_up){
  fatal = 1;}

else{
  
  int position_mm = getDistance(position);
  if (position_mm > travel_limit_mm){
      fatal = 1;
    }
    
  travel_mm = position_mm - (cur_pos_mm - prev_distance_mm);
  if (abs(travel_mm + cur_pos_mm) < travel_limit_mm){
    
    steg = (travel_mm)*33.33333;
    
    if (travel_mm > 0){
      digitalWrite(dirPin,HIGH);}
    else{
      digitalWrite(dirPin,LOW);} 

    int check = 0;
    for(int x = 0; x < abs(steg); x++){
      
      digitalWrite(stepPin,HIGH); 
      delayMicroseconds(wait); 
      digitalWrite(stepPin,LOW); 
      delayMicroseconds(wait);

      if (digitalRead(switchPin) == HIGH){
        delay(50);
        fatal = 1;
        delay(1000);
        break;}
    
      check++;
      //Writes to Rpi 10 times every rotation = every 0.6mm
      if (check == 20){
        //Serial.print(1);
        check = 0;} }


    if (fatal == 0){
      cur_pos_mm = position_mm;    
      delay(100);}} // 0.1 second delay}}

  
  else{
    fatal = 1;}
}

  return fatal;

}

//-----------------------------------------MOVE LEVER---------------------------------------
int lever_drive(int lever_command){

  int fatal = 0;
  int value = 0; 
  lever_up = false;
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
      lever_up = true;
      break;
    case 5:
      value = 170;
      lever_up = true;
      break;
  }
  if (value == 0){
    fatal = 1;
    }
  else{
    lever.write(value);
  }
  return fatal;
}

//-------------------------------------GET DISTANCE IN MM------------------------------------
int getDistance(int new_pos){
  int dist = 400;

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
    
    str_command = Serial.readStringUntil("/r");
    int_command = str_command.toInt();

    int state = int_command/1000000;
    int tray_command = (int_command % 1000000) / 10000;
    int distance_command = (int_command % 10000) / 10;
    int lever_command = int_command % 10;
    
    //initiation command
    if (state == 0){
      initiate(); 
      Serial.println(done);
    }
    
    //Position Query
    else if (state == 6){
      Serial.println(cur_pos_mm);
    }
    
    //Sensor query
    else if (state == 7){ 
      Serial.println(done);
    }
    
    //Lever change command
    else if (state == 8){  
      if (lever_drive(lever_command)==1){
        Serial.println(error);}
      else{
        Serial.println(done);}
    }
    
    //Tray change command 
    else if (state == 1){ 
      if (tray_drive(tray_command, distance_command)==1){
        Serial.println(error);
        }
      else{
        Serial.println(done);
        }
    }
    
    //ERROR
    else{
      Serial.println(error);
    }
    
  }
}
