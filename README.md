# moody

#### Be sure to clone this repo under ```/home/pi/``` since the moody.service file contains a path hardcoded to this location.

### Steps to install:

1) Install git to be able to clone this repository:
      ```
      sudo apt update && sudo apt install git -y
      ```
2) Clone this project:
      ```
      cd /home/pi && git clone https://github.com/Hypno-Crafts/moody.git
      ```
3) Open raspi-config and enable SPI + expand the filesystem:
    - Open a terminal and run:
      ```
      sudo raspi-config
      ```
    - Navigate (using a combination of arrow keys, tab and enter) to: Interfacing Options → SPI
    - Select Enable and confirm.
    - Navigate to: Advanced Options → Expand Filesystem
    - Confirm and navigate to 'finish' and confirm when asked to reboot or reboot manually via:
      ```
      sudo reboot now
      ```
4) Now your ssh connection will be lost, wait for the Raspberry Pi to restart and login via ssh again.
      
5) Once logged in via ssh, execute: 
      ```
      cd /home/pi/moody && chmod +x setup.sh && ./setup.sh
      ```
