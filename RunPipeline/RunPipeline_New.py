import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# RunPipeline
#

class RunPipeline(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "RunPipeline" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# RunPipelineWidget
#

class RunPipelineWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input file selectors
    #
    self.inputSelectors = []
    self.nInputs = 5
    times = ["Pre", "Post1", "Post2", "Post3", "Post4"]
    for i in range(self.nInputs):
      inputSelector = slicer.qMRMLNodeComboBox()
      inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
      inputSelector.selectNodeUponCreation = True
      inputSelector.enabled = True
      inputSelector.addEnabled = False
      inputSelector.removeEnabled = False
      inputSelector.noneEnabled = False
      inputSelector.showHidden = False
      inputSelector.showChildNodeTypes = False
      inputSelector.setMRMLScene( slicer.mrmlScene )
      inputSelector.setToolTip( "Pick the inputs to the algorithm." )
      parametersFormLayout.addRow(times[i], inputSelector)
      self.inputSelectors.append(inputSelector)
    
    #
    # mask volume selector
    #
    self.maskSelector = slicer.qMRMLNodeComboBox()
    self.maskSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.maskSelector.selectNodeUponCreation = True
    self.maskSelector.addEnabled = True
    self.maskSelector.removeEnabled = True
    self.maskSelector.noneEnabled = False
    self.maskSelector.showHidden = False
    self.maskSelector.showChildNodeTypes = False
    self.maskSelector.setMRMLScene( slicer.mrmlScene )
    self.maskSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Mask", self.maskSelector)
            
    #
    # output filename textbox
    #
    self.outputTextbox = qt.QLineEdit("ANNSeg")
    self.outputTextbox.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output file basename", self.outputTextbox)
        

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    pass

  def onApplyButton(self):
    logic = RunPipelineLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    imageThreshold = self.imageThresholdSliderWidget.value
    inputNodes = []
    for i in range(self.nInputs):
      inputNodes.append(self.inputSelectors[i].currentNode())
    logic.run(inputNodes, self.maskSelector.currentNode(), self.outputTextbox.text, enableScreenshotsFlag)

    fgNode = slicer.util.getNode(pattern=self.outputTextbox.text+"_probability")
    labelNode = slicer.util.getNode(pattern=self.outputTextbox.text+"_mask")
    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(inputNodes[1].GetID())
    selectionNode.SetReferenceSecondaryVolumeID(fgNode.GetID())    
    selectionNode.SetReferenceActiveLabelVolumeID(labelNode.GetID())
    appLogic.PropagateVolumeSelection()
    
#
# RunPipelineLogic
#

class RunPipelineLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self, volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() == None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNodes, maskVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNodes:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not maskVolumeNode:
      logging.debug('isValidInputOutputData failed: no mask volume node defined')
      return False      
    if len(inputVolumeNodes) != 5:
      logging.debug('isValidInputOutputData failed: too few inputs selected.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputNodes, maskNode, outputFileBasename, enableScreenshots=0):
    """
    Run the actual algorithm
    """
    if not self.isValidInputOutputData(inputNodes, maskNode):
      slicer.util.errorDisplay('Error.')
      return False

    logging.info('Processing started')

    # Get file names from volume nodes.
    inputFiles = []
    for node in inputNodes:
      filename = node.GetStorageNode().GetFileName()
      inputFiles.append(filename)
    maskFile = maskNode.GetStorageNode().GetFileName()
    
    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    #cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    #cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)
    cmd = 'D:\\Work\\BreastCAD\\Pipeline\\bin\\lesionSegmentation.exe' + \
              ' -a ' + "D:\\Work\\BreastCAD\\Pipeline\\bin\\2_1_NS_NF.txt" + \
              ' -i ' + inputFiles[0] + ' ' + inputFiles[1] + ' ' + \
              inputFiles[2] + ' ' + inputFiles[3] + ' ' + inputFiles[4] + \
              ' -m ' + maskFile + \
              ' -o ' + os.path.dirname(inputFiles[0]) + os.sep + outputFileBasename
    print cmd
    os.environ['ITK_AUTOLOAD_PATH'] = ''
    os.environ['VTK_AUTOLOAD_PATH'] = ''
    result = os.system(cmd)
    print result
    slicer.util.loadVolume(os.path.dirname(inputFiles[0]) + os.sep + 
                           outputFileBasename + "_probability.mha")
    slicer.util.loadLabelVolume(os.path.dirname(inputFiles[0]) + os.sep + 
                                outputFileBasename + "_mask.mha")
    logging.info('Processing completed with result: {}'.format(result))

    return result


class RunPipelineTest(ScriptedLoadableModuleTest):
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
    self.test_RunPipeline1()

  def test_RunPipeline1(self):
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
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = RunPipelineLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
