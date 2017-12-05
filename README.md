# AnkiVideoToFrames
Takes a video then outputs frames and text file to be imported into Anki.
It can either create a certain amount of frames or make a frame every X seconds.
Numbers are only approximate due to mplayer inconsistencies.

Make sure you have these python packages (available through pip):

    pillow
    pyqt5
    
And these programs (available through your distro's package manger, presumably):

    mplayer

&nbsp;

Usage:

1. Start main.py

2. Select your collection.media folder

3. Select the video file

4. Adjust the settings, press "Commence"

5. Import the created csv using the basic note type, making sure to check "Allow HTML in fields"
