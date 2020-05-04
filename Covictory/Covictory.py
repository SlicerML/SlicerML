import base64
import logging
import os
import sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# Covictory
#

class Covictory(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Covictory"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Machine Learning"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Steve Pieper (Isomics, Inc.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
A module for chest X ray analysis and related developments
"""  # TODO: update with short description of the module
    self.parent.helpText += self.getDefaultModuleDocumentationLink()  # TODO: verify that the default URL is correct or change it to the actual documentation
    self.parent.acknowledgementText = """
Collaboration with https://acil.med.harvard.edu/.
Developed in part by NAC: a Biomedical Technology Resource Center supported by the National Institute of Biomedical Imaging and Bioengineering (NIBIB) (P41 EB015902).
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # TODO: replace with organization, grant and thanks.

#
# CovictoryWidget
#

class CovictoryWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/Covictory.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    #
    # overall parameters
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Overall Parameters"
    parametersCollapsibleButton.collapsed = True
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.slowdownPath = ctk.ctkPathLineEdit()
    self.slowdownPath.filters = qt.QDir.Dirs | qt.QDir.Readable
    self.slowdownPath.toolTip = "Where https://github.com/acil-bwh/slowdown-covid19 is checked out"
    self.slowdownPath.currentPath = '/Users/pieper/covictory/slowdown-covid19'
    parametersFormLayout.addRow("Slowdown Path", self.slowdownPath)


    #
    # equalizing parameters
    #
    equalizingCollapsibleButton = ctk.ctkCollapsibleButton()
    equalizingCollapsibleButton.text = "Equalizing"
    self.layout.addWidget(equalizingCollapsibleButton)
    equalizingFormLayout = qt.QFormLayout(equalizingCollapsibleButton)

    self.dataPath = ctk.ctkPathLineEdit()
    self.dataPath.filters = qt.QDir.Dirs | qt.QDir.Files | qt.QDir.Readable
    self.dataPath.currentPath = '/Users/pieper/covictory/site/cxr/samples'
    self.dataPath.setToolTip("Where the input images are stored")
    equalizingFormLayout.addRow("Data path: ", self.dataPath)

    self.loadAndEqualize = qt.QPushButton("Load and Equalize")
    self.dataPath.setToolTip("Loads the images and applies the equalize algorithm")
    equalizingFormLayout.addWidget(self.loadAndEqualize)

    #
    # verification parameters
    #
    verificationCollapsibleButton = ctk.ctkCollapsibleButton()
    verificationCollapsibleButton.text = "Verification"
    self.layout.addWidget(verificationCollapsibleButton)
    verificationFormLayout = qt.QFormLayout(verificationCollapsibleButton)

    self.useLocalServer = qt.QCheckBox("Use local server")
    self.useLocalServer.toolTip = "Launch http://l127.0.0.1:8080"
    self.useLocalServer.checked = True
    verificationFormLayout.addWidget(self.useLocalServer)

    self.launchCovictory = qt.QPushButton("Launch Covictory")
    self.dataPath.setToolTip("Load the site")
    verificationFormLayout.addWidget(self.launchCovictory)


    # Add vertical spacer
    self.layout.addStretch(1)

    # Create a new parameterNode
    # This parameterNode stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.logic = CovictoryLogic()
    self.ui.parameterNodeSelector.addAttribute("vtkMRMLScriptedModuleNode", "ModuleName", self.moduleName)
    self.setParameterNode(self.logic.getParameterNode())

    # Connections
    self.ui.parameterNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setParameterNode)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.slowdownPath.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.dataPath.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

    self.loadAndEqualize.connect("clicked()", self.onLoadAndEqualize)
    self.launchCovictory.connect("clicked()", self.onLaunchCovictory)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def setParameterNode(self, inputParameterNode):
    """
    Adds observers to the selected parameter node. Observation is needed because when the
    parameter node is changed then the GUI must be updated immediately.
    """

    return

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Set parameter node in the parameter node selector widget
    wasBlocked = self.ui.parameterNodeSelector.blockSignals(True)
    self.ui.parameterNodeSelector.setCurrentNode(inputParameterNode)
    self.ui.parameterNodeSelector.blockSignals(wasBlocked)

    if inputParameterNode == self._parameterNode:
      # No change
      return

    # Unobserve previusly selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    if inputParameterNode is not None:
      self.addObserver(inputParameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """
    return

    # Disable all sections if no parameter node is selected
    self.ui.basicCollapsibleButton.enabled = self._parameterNode is not None
    self.ui.advancedCollapsibleButton.enabled = self._parameterNode is not None
    if self._parameterNode is None:
      return

    # Update each widget from parameter node
    # Need to temporarily block signals to prevent infinite recursion (MRML node update triggers
    # GUI update, which triggers MRML node update, which triggers GUI update, ...)

    wasBlocked = self.ui.inputSelector.blockSignals(True)
    self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.inputSelector.blockSignals(wasBlocked)

    wasBlocked = self.ui.outputSelector.blockSignals(True)
    self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    self.ui.outputSelector.blockSignals(wasBlocked)

    wasBlocked = self.invertedOutputSelector.blockSignals(True)
    self.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
    self.invertedOutputSelector.blockSignals(wasBlocked)

    wasBlocked = self.ui.imageThresholdSliderWidget.blockSignals(True)
    self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
    self.ui.imageThresholdSliderWidget.blockSignals(wasBlocked)

    wasBlocked = self.ui.invertOutputCheckBox.blockSignals(True)
    self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")
    self.ui.invertOutputCheckBox.blockSignals(wasBlocked)

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
      self.ui.applyButton.toolTip = "Compute output volume"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input and output volume nodes"
      self.ui.applyButton.enabled = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None:
      return

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
    self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
    self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
    self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.invertedOutputSelector.currentNodeID)

  def onLoadAndEqualize(self):
    try:
      if not self.logic.webWidget:
        self.onLaunchCovictory()
      self.logic.loadAndEqualize(self.slowdownPath.currentPath, self.dataPath.currentPath)
    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()

  def onLaunchCovictory(self):
    if self.useLocalServer.checked:
        url = "http://localhost:8080"
    else:
      url = "https://covictory.dev"
    self.logic.launchCovictory(url)

#
# CovictoryLogic
#

class CovictoryLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleLogic.__init__(self, parent)
    self.webWidget = None

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "50.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def loadAndEqualize(self, slowdownPath, dataPath):

    codePath = slowdownPath+"/equalization"
    if codePath not in sys.path:
      sys.path.append(codePath)

    import equlize_cxr as eq
    import skimage.color

    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    origID = shNode.CreateFolderItem(shNode.GetSceneItemID(), "Original")
    equalID = shNode.CreateFolderItem(shNode.GetSceneItemID(), "Equalized")

    cxr_files = eq.listdir(dataPath)

    cxr_files[1:]

    origNodes = []

    self.delayDisplay(f"Python processing", 500)
    for cxr_file in cxr_files:
      self.delayDisplay(f"Processing {cxr_file}", 200)
      path = eq.join(dataPath, cxr_file)
      name = os.path.splitext(cxr_file)[0]
      try:
        img = eq.image.imread(path)
      except Exception:
        logging.info(f"skipping {cxr_file}")
        continue

      imggray = skimage.color.rgb2gray(img).astype('float32')
      imgeq = eq.equalize(imggray)
      eqPath = eq.join(slicer.app.temporaryPath, name+".png")
      eq.io.imsave(eqPath, imgeq)

      loadProperties = {'singleFile': True}
      loader = lambda path: slicer.util.loadVolume(path, properties=loadProperties)
      origNode = loader(path)
      equalNode = loader(eqPath)
      shNode.SetItemParent(shNode.GetItemByDataNode(origNode), origID)
      shNode.SetItemParent(shNode.GetItemByDataNode(equalNode), equalID)
      origNodes.append(origNode)

    self.delayDisplay(f"JavaScript processing {cxr_file}", 500)
    for origNode in origNodes:
      imageArray = slicer.util.arrayFromVolume(origNode) 
      rows = imageArray.shape[1]
      columns = imageArray.shape[2]
      imageString = str(base64.b64encode(imageArray))[2:-1]
      self.webWidget.evalJS(f"""
        predictFromBase64Image(`{origNode.GetName()}`, {rows}, {columns}, `{imageString}`);
      """)

    logging.info('Processing completed')

  def launchCovictory(self, url):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalWidescreenView)
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalView)
    splitter = lm.threeDWidget(0).parent()
    self.webWidget = slicer.qSlicerWebWidget()
    self.webWidget.url = url
    splitter = lm.threeDWidget(0).parent()
    splitter.insertWidget(0, self.webWidget)
    lm.threeDWidget(0).hide()
    sizes = [int(splitter.height*.67), 0, int(splitter.height*.33)]
    splitter.setSizes(sizes)


#
# CovictoryTest
#

class CovictoryTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Covictory1()

  def test_Covictory1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    inputVolume = SampleData.downloadFromURL(
      nodeNames='MRHead',
      fileNames='MR-Head.nrrd',
      uris='https://github.com/Slicer/SlicerTestingData/releases/download/MD5/39b01631b7b38232a220007230624c8e',
      checksums='MD5:39b01631b7b38232a220007230624c8e')[0]
    self.delayDisplay('Finished with download and loading')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 279)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 50

    # Test the module logic

    logic = CovictoryLogic()

    # Test algorithm with non-inverted threshold
    logic.run(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.run(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
