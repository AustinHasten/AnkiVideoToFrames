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
        self.check_mpv()
        self.set_model()
        
        self.inputPath = None

        self.buildGUI()

        # Simulate file select button push
        self.fileSelectBtnPushed()

    def check_mpv(self):
        self.mpv = 'mpv'
        if utils.isWin:
            self.mpv = os.path.join(os.path.dirname(sound.mpvPath[0]), 'mpv.com')
        mplayer_test = utils.call([self.mpv, '-V', '--no-terminal'])
        if mplayer_test == -1:
            showInfo('MPV not found.')
            self.close()

    def set_model(self):
        # Check for 'Basic' note type, create it if it doesn't exist
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
        # Create window and layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

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

        # Add widgets to layout
        self.layout.addWidget(self.intervalLbl, 0, 0)
        self.layout.addWidget(self.intervalSpin, 0, 1)
        self.layout.addWidget(self.totalFramesLbl, 1, 0)
        self.layout.addWidget(self.totalFramesSpin, 1, 1)
        self.layout.addWidget(self.fileSelectBtn, 2, 0)
        self.layout.addWidget(self.commenceBtn, 2, 1)

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
        startupinfo = sp.STARTUPINFO()
        startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
        results = sp.check_output(command, startupinfo=startupinfo).decode('utf-8')
        self.videoLength = int(re.search(r'LENGTH=(\d*)', results).groups()[0])

        # Move spinbox ranges
        self.intervalSpin.setRange(1, self.videoLength)
        self.totalFramesSpin.setRange(1, self.videoLength)

    # Link values of delay and total shots
    def intervalSpinChanged(self):
        totalShots = (self.videoLength / self.intervalSpin.value())
        self.totalFramesSpin.setValue(totalShots)

    # Link values of delay and total shots
    def totalFramesSpinChanged(self):
        interval = (self.videoLength / self.totalFramesSpin.value())
        self.intervalSpin.setValue(interval)

    def commenceBtnPushed(self):
        if not self.inputPath:
            return

        baseName = os.path.basename(self.inputPath)
        fileName, fileExtension = os.path.splitext(baseName)

        tmpDir = utils.tmpdir()
        command = [
            self.mpv, '--vo=image', f'--vo-image-outdir={tmpDir}',
            '-sstep', str(self.intervalSpin.value()), self.inputPath]
        self.setEnabled(False)
        mw.app.processEvents()
        utils.call(command)

        for frame in os.listdir(tmpDir):
            newPath = os.path.join(mw.col.media.dir(), f'{fileName}_{frame}')
            shutil.move(os.path.join(tmpDir, frame), newPath)

            note = mw.col.newNote()
            note['Front'] = f'<img src=\"{fileName}_{frame}\">'
            note['Back'] = fileName
            note.tags.append('videotoframes')
            mw.col.addNote(note)

        self.setEnabled(True)

def start():
    mw.myWidget = widget = App()
    widget.show()

action = QAction('VideoToFrames', mw)
action.triggered.connect(start)
mw.form.menuTools.addAction(action)
