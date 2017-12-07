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

        basicModel = mw.col.models.byName('Basic')
        if not basicModel:
            # TODO Create Basic note type
            showInfo('No Basic note type')
            return
        mw.col.models.setCurrent(basicModel)

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
        self.progressBar = QProgressBar()

        # Connect signals to slots
        self.fileSelectBtn.pressed.connect(self.fileSelectBtnPushed)
        self.intervalSpin.valueChanged.connect(self.intervalSpinChanged)
        self.totalFramesSpin.valueChanged.connect(self.totalFramesSpinChanged)
        self.commenceBtn.pressed.connect(self.commenceBtnPushed)

        # Add toggle widgets to list
        self.toggleWidgets = [
            self.intervalSpin,
            self.totalFramesSpin,
            self.fileSelectBtn,
            self.commenceBtn]

        # Disable widgets
        self.setToggleWidgets(False)

        # Add widgets to layout
        self.layout.addWidget(self.intervalLbl, 0, 0)
        self.layout.addWidget(self.intervalSpin, 0, 1)
        self.layout.addWidget(self.totalFramesLbl, 1, 0)
        self.layout.addWidget(self.totalFramesSpin, 1, 1)
        self.layout.addWidget(self.fileSelectBtn, 2, 0)
        self.layout.addWidget(self.commenceBtn, 2, 1)
        self.layout.addWidget(self.progressBar, 3, 0, 1, 2)

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
            'mpv',
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
        # Calculate total shots by dividing video length by shot interval
        totalShots = (self.videoLength / self.intervalSpin.value())
        self.totalFramesSpin.setValue(totalShots)

    # Link values of delay and total shots
    def totalFramesSpinChanged(self):
        # Calculate interval by dividing video length by total shots
        interval = (self.videoLength / self.totalFramesSpin.value())
        self.intervalSpin.setValue(interval)

    def commenceBtnPushed(self):
        # Seperate file name and file extension
        baseName = os.path.basename(self.inputPath)
        fileName, fileExtension = os.path.splitext(baseName)

        # Delete and recreate temporary directory
        tmpDir = mw.col.media.dir() + '/avtf_tmp'
        if os.path.exists(tmpDir):
            shutil.rmtree(tmpDir)
        os.makedirs(tmpDir)

        command = ['mpv',
            '--vo=image', f'--vo-image-outdir={tmpDir}',
            '-sstep', str(self.intervalSpin.value()),
            self.inputPath]
        pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)

        # Disable widgets and start indeterminate progressbar
        self.setToggleWidgets(False)
        self.progressBar.setRange(0, 0)

        # Continually check if pipe has completed and update GUI
        while pipe.returncode == None:
            pipe.poll()
            self.processEvents()

        for frame in os.listdir(tmpDir):
            # Prefix file names with movie's title and move them to media folder
            newPath = f'{mw.col.media.dir()}/{fileName}_{frame}'
            shutil.move(f'{tmpDir}/{frame}', newPath)
            note = mw.col.newNote()
            note['Front'] = f'<img src=\"{fileName}_{frame}\">'
            note['Back'] = fileName
            mw.col.addNote(note)

        # Delete temporary directory
        shutil.rmtree(tmpDir)

        # Reenable widgets and stop indeterminate progressbar
        self.progressBar.setRange(0, 1)
        self.setToggleWidgets(True)

def start():
    mplayer_test = utils.call(['mplayer', '-really-quiet'])
    if mplayer_test == -1:
        showInfo('MPlayer not found.')
        return
    mw.myApp = app = App(sys.argv)

action = QAction("test", mw)
action.triggered.connect(start)
mw.form.menuTools.addAction(action)
