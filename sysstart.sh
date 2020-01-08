#!/bin/bash
filename="GreatShot"

cd /home/megarobo

#LED_GREEN2->GPIO4
#LED_RED1->GPIO3
#LED_GREEN1->GPIO2
led_light()
{
	#create directory gpio4
	echo $1 > /sys/class/gpio/export 
	#setting gpio4 direct
	echo out > /sys/class/gpio/gpio$1/direction
	#set the value
	echo $2 > /sys/class/gpio/gpio$1/value
}

net_check()
{
	eth0_enable=$(cat /sys/class/net/eth0/carrier)
	
	if [ "$eth0_enable"x = "1"x ];then
		ifconfig wlan0 down
		ifconfig eth0 down					
		ifconfig eth0  up
	fi
}

start_program()
{
	if [ -f "./MRH-T/update.src/$filename" ];then
	echo "$filename is found.\n" > /dev/ttyAMA0
	cp -rf ./MRH-T/$filename ./MRH-T/update.back &&
	cp -rf ./MRH-T/update.src/$filename ./MRH-T &&
	chmod 755 ./MRH-T/$filename &&
	rm -rf ./MRH-T/update.src/$filename &&
	sync &&
	sync &&
	sync
	else
	echo "$filename is not found." > /dev/ttyAMA0
	fi	

	if [ -x "./MRH-T/$filename" ];then
	./MRH-T/$filename &
	else
		echo "Do not exist $filename \n" >/dev/ttyAMA0 
	fi
}

start_py()
{
	if [ -x "./MRH-T/script/pystart.sh" ];then
	./MRH-T/script/pystart.sh &
	fi
}

#net_check
start_program
start_py
#led_light 16 0

