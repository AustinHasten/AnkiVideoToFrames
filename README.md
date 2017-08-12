# AnkiVideoToFrames
Takes a video then outputs frames and text file to be imported into Anki.
It can either create a certain amount of frames or make a frame every X seconds.
Numbers are only approximate due to mplayer inconsistencies.

Make sure you have these python packages (available through pip):

    wand
    pyqt5
    
And these programs (available through your distro's package manger, presumably):

    mplayer
    imagemagick

&nbsp;

Frames are outputted to the Anki collection.media folder that you select on startup.
The file names are formatted in this way:

    Movie Title_Frame Number.jpg
    
    EX.
    Bride of Frankenstein_00000093.jpg
    
&nbsp;

The outputted text file is a csv where each line looks like this:

    Input File Name;Frame Number.jpg
    
&nbsp;

So you cards should look like this:

Front:

    <img src="{{Title}}_{{Frame Number}}">

Back:

    {{FrontSide}}
    
    <hr id="answer">
    
    {{Title}}
