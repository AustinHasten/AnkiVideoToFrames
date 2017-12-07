# Saul Femm
# Initial Commit - August 11th, 2017

import os, sys, shutil, re
import subprocess as sp
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from anki import utils

class App(QApplication):
    def __init__(self, args):
        super().__init__(args)

        self.mpv = 'mpv'
        if utils.isWin:
            self.mpv = os.path.join(os.path.dirname(sys.executable), 'mpv.com')

        self.buildGUI()

    def buildGUI(self):
        # Create window and layout
        self.window = QWidget()
        self.layout = QGridLayout()
        self.window.setLayout(self.layout)

        # Create widgets
        self.intervalLbl = QLabel("Seconds between frames: ")
        self.intervalSpin = QSpinBox()
        self.totalFramesLbl = QLabel("Total number of frames: ")
        self.totalFramesSpin = QSpinBox()
        self.fileSelectBtn = QPushButton("Select file...")
        self.commenceBtn = QPushButton("Commence")

        # Connect signals to slots
        self.fileSelectBtn.pressed.connect(self.fileSelectBtnPushed)
        self.intervalSpin.valueChanged.connect(self.intervalSpinChanged)
        self.totalFramesSpin.valueChanged.connect(self.totalFramesSpinChanged)
        self.commenceBtn.pressed.connect(self.commenceBtnPushed)

        # Add toggle widgets to list
        self.toggleWidgets = [
            self.intervalSpin, self.totalFramesSpin,
            self.fileSelectBtn, self.commenceBtn]

        # Disable toggle widgets
        self.setToggleWidgets(False)

        # Add widgets to layout
        self.layout.addWidget(self.intervalLbl, 0, 0)
        self.layout.addWidget(self.intervalSpin, 0, 1)
        self.layout.addWidget(self.totalFramesLbl, 1, 0)
        self.layout.addWidget(self.totalFramesSpin, 1, 1)
        self.layout.addWidget(self.fileSelectBtn, 2, 0)
        self.layout.addWidget(self.commenceBtn, 2, 1)

        # Simulate file select button push
        self.fileSelectBtnPushed()

        # Display app
        self.window.show()

    def setToggleWidgets(self, state):
        for widget in self.toggleWidgets:
            widget.setEnabled(state)

    def fileSelectBtnPushed(self):
        # Open file dialog to choose video
        self.inputPath = \
            QFileDialog.getOpenFileName(
                    caption='Select Video File',
                    filter='Video Files (*.avi *.flv *.mkv *.mp4 *.mpg *.wmv)')[0]

        # Use mpv to get video length
        command = [
            self.mpv,
            '--term-playing-msg=\"LENGTH=${=duration}\"',
            '--vo=null', '--ao=null',
            '--frames=1', '--no-cache', '--no-config',
            '--quiet', self.inputPath]
        results = sp.check_output(command).decode('utf-8')
        self.videoLength = int(re.search(r'LENGTH=(\d*)', results).groups()[0])

        # Move spinbox ranges
        self.intervalSpin.setRange(1, self.videoLength)
        self.totalFramesSpin.setRange(1, self.videoLength)

        # Enable widgets
        self.setToggleWidgets(True)

    # Link values of delay and total shots
    def intervalSpinChanged(self):
        totalShots = (self.videoLength / self.intervalSpin.value())
        self.totalFramesSpin.setValue(totalShots)

    # Link values of delay and total shots
    def totalFramesSpinChanged(self):
        interval = (self.videoLength / self.totalFramesSpin.value())
        self.intervalSpin.setValue(interval)

    def commenceBtnPushed(self):
        baseName = os.path.basename(self.inputPath)
        fileName, fileExtension = os.path.splitext(baseName)

        tmpDir = utils.tmpdir()
        command = [
            self.mpv, '--vo=image', f'--vo-image-outdir={tmpDir}',
            '-sstep', str(self.intervalSpin.value()), self.inputPath]
        self.setToggleWidgets(False)
        self.processEvents()
        utils.call(command)

        for frame in os.listdir(tmpDir):
            newPath = os.path.join(mw.col.media.dir(), f'{fileName}_{frame}')
            shutil.move(os.path.join(tmpDir, frame), newPath)
            note = mw.col.newNote()
            note['Front'] = f'<img src=\"{fileName}_{frame}\">'
            note['Back'] = fileName
            mw.col.addNote(note)

        self.setToggleWidgets(True)

def start():
    # Check that mpv is available
    mpv = 'mpv'
    if utils.isWin:
        mpv = os.path.dirname(sys.executable) + '\mpv.com'

    mplayer_test = utils.call([mpv, '-V', '--really-quiet'])
    if mplayer_test == -1:
        showInfo('MPV not found.')
        return

    # Check for 'Basic' note type
    # TODO Create Basic note type if it doesn't exist
    basicModel = mw.col.models.byName('Basic')
    if not basicModel:
        showInfo('No Basic note type')
        return
    mw.col.models.setCurrent(basicModel)

    mw.myApp = app = App(sys.argv)

action = QAction('VideoToFrames', mw)
action.triggered.connect(start)
mw.form.menuTools.addAction(action)

