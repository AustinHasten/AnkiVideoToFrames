# Saul Femm
# Initial Commit - August 11th, 2017

import os
import sys
import shutil
import subprocess as sp

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSpinBox, \
        QPushButton, QProgressBar, QGridLayout, QFileDialog
from PyQt5.QtGui import QFont, QFontDatabase

import midentify

from wand.image import Image
from wand.color import Color


class tmp(QApplication):
    def __init__(self, args):
        super().__init__(args)

        # Black image used to compare frames with to make sure they aren't blank
        self.blackImage = Image(width=1, height=1, background=Color('black'))

        self.buildGui()

    def buildGui(self):
        # Create window and layout
        self.window = QWidget()
        self.layout = QGridLayout()
        self.window.setLayout(self.layout)

        # Create widgets
        self.intervalLabel = QLabel("Seconds between frames: ")
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
        self.toggleWidgets = []
        self.toggleWidgets.append(self.intervalSpin)
        self.toggleWidgets.append(self.totalFramesSpin)
        self.toggleWidgets.append(self.fileSelectBtn)
        self.toggleWidgets.append(self.commenceBtn)

        # Disable widgets
        self.setToggleWidgets(False)

        # Add widgets to layout
        self.layout.addWidget(self.intervalLabel, 0, 0)
        self.layout.addWidget(self.intervalSpin, 0, 1)
        self.layout.addWidget(self.totalFramesLbl, 1, 0)
        self.layout.addWidget(self.totalFramesSpin, 1, 1)
        self.layout.addWidget(self.fileSelectBtn, 2, 0)
        self.layout.addWidget(self.commenceBtn, 2, 1)
        self.layout.addWidget(self.progressBar, 3, 0, 1, 2)

        # Set font for the whole application
        QFontDatabase.addApplicationFont('terminus.ttf')
        self.setFont(QFont('Terminus (TTF)', 14))

        # Open media folder and input file select dialogs
        self.mediaFolder = \
            QFileDialog.getExistingDirectory(caption="Select Anki Media Folder")
        self.fileSelectBtnPushed()

        # Display app
        self.window.show()
        self.window.resize(350, 150)

    def setToggleWidgets(self, state):
        for widget in self.toggleWidgets:
            widget.setEnabled(state)

    def fileSelectBtnPushed(self):
        # Open file dialog to choose video
        self.inputPath = \
            QFileDialog.getOpenFileName(
                    caption='Select Video File',
                    filter='Video Files (*.avi *.flv *.mkv *.mp4 *.mpg *.wmv)')[0]

        # Use ffprobe to get video length
        self.videoLength = int(midentify.midentify(self.inputPath).length)

        # Move spinbox ranges
        self.intervalSpin.setRange(1, self.videoLength)
        self.totalFramesSpin.setRange(1, self.videoLength)

        # Enable widgets
        self.setToggleWidgets(True)

    # Link values of deley and total shots
    def intervalSpinChanged(self):
        # Calculate total shots by dividing video length by shot interval
        total_shots = (self.videoLength / self.intervalSpin.value())
        self.totalFramesSpin.setValue(total_shots)

    # Link values of deley and total shots
    def totalFramesSpinChanged(self):
        # Calculate interval by dividing video length by total shots
        interval = (self.videoLength / self.totalFramesSpin.value())
        self.intervalSpin.setValue(interval)

    def commenceBtnPushed(self):
        # Seperate file name and file extension
        baseName = os.path.basename(self.inputPath)
        fileName, fileExtension = os.path.splitext(baseName)

        # Create directory to hold frames before they're renamed
        if not os.path.exists('tmp'):
            os.makedirs('tmp')

        command = [ 
                'mplayer',
                '-vo', 'jpeg:outdir=tmp',
                '-sstep', str(self.intervalSpin.value()),
                '-endpos', str(self.videoLength),
                self.inputPath]
        pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)

        # Disable widgets and start indeterminate progressbar
        self.setToggleWidgets(False)
        self.progressBar.setRange(0, 0)

        # Continually check if pipe has completed and update GUI
        while pipe.returncode == None:
            pipe.poll()
            self.processEvents()

        # Loop over the files created
        with open(f'./csv/{fileName}.csv', 'w') as csv:
            for frame in os.listdir('./tmp'):
                # Prefix file names with movie's title and move them to media folder
                newPath = f'{self.mediaFolder}/{fileName}_{frame}'
                shutil.move(f'./tmp/{frame}', newPath)

                # Find blank images and delete them, write non-blank file info
                with Image(filename=newPath) as img:
                    mean = img.compare(self.blackImage, 'mean_absolute')[1]
                    if mean == 0.0:
                        os.remove(newPath)
                    else:
                        csv.write(f'{fileName};{frame}\n')

        # Reenable widgets and stop indeterminate progressbar
        self.progressBar.setRange(0, 1)
        self.setToggleWidgets(True)

if __name__ == '__main__':
    app = tmp(sys.argv)
    sys.exit(app.exec_())
