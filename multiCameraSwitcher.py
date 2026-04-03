moduleName = 'multiCameraSwitcher'
moduleVersion = 1.1
moduleNameLong = 'Multi Camera Switcher'
moduleUrl = 'https://github.com/PrewizardsStudio/multi-camera-switcher'
moduleIconUrl = 'https://github.com/PrewizardsStudio/multi-camera-switcher/blob/main/multiCameraSwitcher.png?raw=true'
moduleCommand = """
import maya.cmds as cmds

def getPySideVersion():
    import sys
    
    if 'PySide' in sys.modules:
        return 'PySide'
    elif 'PySide2' in sys.modules:
        return 'PySide2'
    elif 'PySide6' in sys.modules:
        return 'PySide6'

def initQT():
    import maya.OpenMayaUI as mui
    
    PySideVersion = getPySideVersion()
    
    if PySideVersion == 'PySide':
        PySideVersion = 'PySide'
        from PySide import QtGui, QtCore
        from preDevelopment.Qt.Qt import QtWidgets
        from shiboken import wrapInstance
    elif PySideVersion == 'PySide2':
        PySideVersion = 'PySide2'
        from PySide2 import QtGui, QtWidgets, QtCore
        from PySide2.QtWidgets import QAction
        from shiboken2 import wrapInstance
    elif PySideVersion == 'PySide6':
        PySideVersion = 'PySide6'
        from PySide6 import QtGui, QtWidgets, QtCore
        from PySide6.QtGui import QAction
        from shiboken6 import wrapInstance
 
    return mui, QtGui, QtCore, QtWidgets, wrapInstance, QAction

mui, QtGui, QtCore, QtWidgets, wrapInstance, QAction = initQT()

def getMainWindow(mui, QtGui, QtCore, QtWidgets, wrapInstance):
    main_window_ptr = mui.MQtUtil.mainWindow()
    if getPySideVersion() == 'PySide':
        mainWin = wrapInstance(long(main_window_ptr), QtGui.QWidget)
    else:
        import sys
        if sys.version_info[0] < 3:
            mainWin = wrapInstance(long(main_window_ptr), QtWidgets.QWidget)  
        else:            
            mainWin = wrapInstance(int(main_window_ptr), QtWidgets.QWidget) 
    return mainWin

class multiCameraSwitcher(QtWidgets.QMainWindow):
    def closeExistingWindow(self):
        for qt in QtWidgets.QApplication.topLevelWidgets():
            try:
                if qt.__class__.__name__ == self.__class__.__name__:
                    qt.close()
            except:
                pass

    def __init__(self, parent = getMainWindow(mui, QtGui, QtCore, QtWidgets, wrapInstance)):        
        self.closeExistingWindow()
        QtWidgets.QMainWindow.__init__(self, parent)
        self.recallFrame = False
        self.recallRange = False
        self.initUI()

    def initUI(self):        
        # create window
        self.setWindowTitle('Cam Switcher')
        #self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.resize(60, 300)
        self.statusBar().setSizeGripEnabled(False)
        self.centerWidget = QtWidgets.QWidget()
        self.hbox = QtWidgets.QHBoxLayout()
        
        self.cameraList = QtWidgets.QListWidget(self)
        self.cameraList.itemSelectionChanged.connect(self.selectCamera)     
        self.cameraList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        QtCore.QObject.connect(self.cameraList, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.cameraContextMenu)
        
        for camName in self.getSceneCameras():            
            item = QtWidgets.QListWidgetItem(camName.replace('Shape', ''), self.cameraList) 
            item.setToolTip(camName)      
        self.activeCamera = None
        self.hbox.addWidget(self.cameraList)
        self.centerWidget.setLayout(self.hbox)
        self.setCentralWidget(self.centerWidget)  
        
        self.show()
          
    def cameraContextMenu(self, point):
        # create context menu
        self.popMenu = QtWidgets.QMenu(self)
        actRecallFrame = QAction('Recall Frame', self)
        actRecallFrame.setCheckable(True)
        actRecallFrame.setChecked(self.recallFrame)
        actRecallRange = QAction('Recall Range', self)
        actRecallRange.setCheckable(True)
        actRecallRange.setChecked(self.recallRange)
        self.popMenu.addAction(actRecallFrame)
        self.popMenu.addAction(actRecallRange)
        actRecallFrame.triggered.connect(self.toggleRecall)
        actRecallRange.triggered.connect(self.toggleRecall)                
        # show context menu
        self.popMenu.exec_(self.cameraList.mapToGlobal(point))
    
    def toggleRecall(self):
        senderObject = self.sender()
        if senderObject.text() == 'Recall Frame':
            self.recallFrame = not self.recallFrame
        elif senderObject.text() == 'Recall Range':
            self.recallRange = not self.recallRange
    
    def getSceneCameras(self):
        sceneCameras = cmds.ls(cameras = True)
        excludedCameras = [u'frontShape', u'perspShape', u'sideShape', u'topShape']
        return sorted(set(sceneCameras) - set(excludedCameras))
    
    def selectCamera(self):
        cameraPanel = self.getActivePanel()
        if cameraPanel:
            if self.activeCamera:
                # store camera frame
                if not cmds.attributeQuery( 'lastFrame', node=self.activeCamera, exists=True ):
                    cmds.addAttr(self.activeCamera, longName = 'lastFrame', attributeType = 'long', keyable = True)
                cmds.setAttr(self.activeCamera + '.lastFrame', int(cmds.currentTime(query=1))) 
                # store camera range
                if not cmds.attributeQuery( 'range', node=self.activeCamera, exists=True ):
                    cmds.addAttr(self.activeCamera, longName = 'range', dataType = "string", keyable = True)
                cmds.setAttr(self.activeCamera + '.range', str(int(cmds.playbackOptions(min = True, query = True))) + '-' + str(int(cmds.playbackOptions(max = True, query = True))), type='string')      
            self.activeCamera = self.cameraList.selectedItems()[0].text()
            selectedCameraShape = str(self.cameraList.selectedItems()[0].toolTip())
            cmds.modelPanel(cameraPanel, edit = True, camera = selectedCameraShape)
            # recall frame
            if self.recallFrame and cmds.attributeQuery( 'lastFrame', node=self.activeCamera, exists=True ):
                cmds.currentTime(cmds.getAttr(self.activeCamera + '.lastFrame'))
            #recall range
            if self.recallRange and cmds.attributeQuery( 'range', node=self.activeCamera, exists=True ):
                cmds.playbackOptions(min = int(cmds.getAttr(self.activeCamera + '.range').split('-')[0]), animationStartTime=int(cmds.getAttr(self.activeCamera + '.range').split('-')[0]), edit = True)
                cmds.playbackOptions(max = int(cmds.getAttr(self.activeCamera + '.range').split('-')[1]), animationEndTime=int(cmds.getAttr(self.activeCamera + '.range').split('-')[1]), edit = True)
            
    def getActivePanel(self):
        if cmds.getPanel(typeOf = cmds.getPanel( withFocus=True )) == 'modelPanel':
            self.statusBar().showMessage('')
            return cmds.getPanel( withFocus=True )
        else:
            self.statusBar().setStyleSheet('QStatusBar {color: rgb(255, 0, 0)}')
            self.statusBar().showMessage('Select model panel')
            return None

myMultiCameraSwitcher = multiCameraSwitcher()
"""

def onMayaDroppedPythonFile(args):
    import sys
    del sys.modules[moduleName]
    installScript()
    
def installScript():
    import os
    import urllib.request
    import maya.mel as mel
    import maya.cmds as cmds

    iconImageName = moduleIconUrl.split('/')[-1].replace('?raw=true','')

    # Get current maya version
    version = cmds.about(version=True)

    # Download Icon
    appPath = os.environ['MAYA_APP_DIR']
    iconPath = os.path.join(appPath, version, "prefs/icons", iconImageName)

    if not os.path.exists(iconPath):
        urllib.request.urlretrieve(moduleIconUrl, iconPath) 

    # Add to current shelf
    topShelf = mel.eval('$nul = $gShelfTopLevel')
    currentShelf = cmds.tabLayout(topShelf, q=1, st=1)
    cmds.shelfButton(parent=currentShelf, image=iconPath, command=moduleCommand, label=moduleNameLong, annotation=moduleNameLong)