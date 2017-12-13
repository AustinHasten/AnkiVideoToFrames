# Saul Femm
# Initial Commit - August 11th, 2017

import os, sys, shutil, re
import subprocess as sp
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from anki import utils, sound

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.inputVideo = ''

        self.checkMPV()
        self.setModel()
        self.buildGUI()

    def checkMPV(self):
        # Look for 'mpv' in PATH on Linux systems
        self.mpv = 'mpv'
        # Look for 'mpv.com' in Anki install directory on Windows systems
        if utils.isWin:
            self.mpv = os.path.join(os.path.dirname(sound.mpvPath[0]), 'mpv.com')

        # Useless command to test mpv.
        mplayer_test = utils.call([self.mpv, '-V', '--no-terminal'])

        # Return code of -1 indicates command not found.
        if mplayer_test == -1:
            showInfo('MPV not found.')
            self.close()

    def setModel(self):
        """ Check for 'Basic' note type, recreate it if it doesn't exist. """
        basicModel = mw.col.models.byName('Basic')
        if not basicModel:
            basicModel = mw.col.models.new('Basic')

            basicTemplate = mw.col.models.newTemplate('Card 1')
            basicTemplate['qfmt'] = '{{Front}}'
            basicTemplate['afmt'] = '{{FrontSide}}\n\n<hr id="answer">\n\n{{Back}}'
            mw.col.models.addTemplate(basicModel, basicTemplate)

            frontField = mw.col.models.newField('Front')
            mw.col.models.addField(basicModel, frontField)

            backField = mw.col.models.newField('Back')
            mw.col.models.addField(basicModel, backField)

            mw.col.models.add(basicModel)
        mw.col.models.setCurrent(basicModel)

    def buildGUI(self):
        # Create window and layout.
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Create widgets.
        self.intervalSpin = QSpinBox()
        self.intervalSpin.setRange(0, 0)
        self.totalFramesSpin = QSpinBox()
        self.totalFramesSpin.setRange(0, 0)
        self.fileSelectBtn = QPushButton("Select file...")
        self.commenceBtn = QPushButton("Commence")

        # Connect signals to slots.
        self.fileSelectBtn.pressed.connect(self.fileSelectBtnPushed)
        self.intervalSpin.valueChanged.connect(self.intervalSpinChanged)
        self.totalFramesSpin.valueChanged.connect(self.totalFramesSpinChanged)
        self.commenceBtn.pressed.connect(self.commenceBtnPushed)

        # Add widgets to layout.
        self.layout.addWidget(QLabel('Seconds between frames: '), 0, 0)
        self.layout.addWidget(self.intervalSpin, 0, 1)
        self.layout.addWidget(QLabel('Total number of frames: '), 1, 0)
        self.layout.addWidget(self.totalFramesSpin, 1, 1)
        self.layout.addWidget(self.fileSelectBtn, 2, 0)
        self.layout.addWidget(self.commenceBtn, 2, 1)

    def fileSelectBtnPushed(self):
        """ Open dialog to get video file, use mpv to get its length. """
        # Open file dialog.
        newVideo = \
            QFileDialog.getOpenFileName(
                caption='Select Video File',
                filter='Video Files (*.avi *.flv *.mkv *.mp4 *.mpg *.wmv)')[0]

        if not newVideo:
            return
        else:
            self.inputVideo = newVideo

        # Set file select button's text to the video file's name.
        self.fileSelectBtn.setText(os.path.basename(self.inputVideo))

        # mpv command to print video length.
        command = [
            self.mpv,
            '--term-playing-msg=\"LENGTH=${=duration}\"',
            '--vo=null', '--ao=null',
            '--frames=1', '--no-cache', '--no-config',
            '--quiet', self.inputVideo]

        # Prevent mpv window from showing on Windows machines.
        if utils.isWin:
            startupinfo = sp.STARTUPINFO()
            startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
        else:
            startupinfo = None

        # Run command, use regex to get video length from output.
        results = sp.check_output(command, startupinfo=startupinfo).decode('utf-8')
        self.videoLength = int(re.search(r'LENGTH=(\d*)', results).groups()[0])

        # Set spinbox ranges based on video length.
        self.intervalSpin.setRange(1, self.videoLength)
        self.totalFramesSpin.setRange(1, self.videoLength)

    def intervalSpinChanged(self):
        """ Link values of delay and total shots. """
        totalShots = (self.videoLength / self.intervalSpin.value())
        self.totalFramesSpin.setValue(totalShots)

    def totalFramesSpinChanged(self):
        """ Link values of delay and total shots. """
        interval = (self.videoLength / self.totalFramesSpin.value())
        self.intervalSpin.setValue(interval)

    def commenceBtnPushed(self):
        """ Split video, move frames to media folder, create a note. """
        if not self.inputVideo:
            return

        baseName = os.path.basename(self.inputVideo)
        fileName, fileExtension = os.path.splitext(baseName)

        # MPV command to split a video into frames
        tmpDir = utils.tmpdir()
        command = [self.mpv, '--vo=image', f'--vo-image-outdir={tmpDir}',
            '-sstep', str(self.intervalSpin.value()), self.inputVideo]

        # Disable all widgets while command runs
        self.setEnabled(False)
        mw.app.processEvents()

        # Perform the command
        utils.call(command)

        for frame in os.listdir(tmpDir):
            # Move frame to media.collection/filename_frame.jpg
            newVideo = os.path.join(mw.col.media.dir(), f'{fileName}_{frame}')
            shutil.move(os.path.join(tmpDir, frame), newVideo)

            # Add note of basic type with image on front and filename on back
            note = mw.col.newNote()
            note['Front'] = f'<img src=\"{fileName}_{frame}\">'
            note['Back'] = fileName
            note.tags.append('videotoframes')
            mw.col.addNote(note)

        # Reenable all widgets now that the work is done
        self.setEnabled(True)

def start():
    mw.myWidget = widget = App()
    widget.show()

action = QAction('VideoToFrames', mw)
action.triggered.connect(start)
mw.form.menuTools.addAction(action)
