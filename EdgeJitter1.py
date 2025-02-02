import adsk.core, adsk.fusion, adsk.cam, traceback
import json
import os
import random
from datetime import datetime
import re  # Import regular expressions
from enum import Enum, auto

class Direction(Enum):
    POSITIVE_X = auto()
    NEGATIVE_X = auto()
    POSITIVE_Y = auto()
    NEGATIVE_Y = auto()

class JitterProcessor:
    # ----- CONSTANTS -----
    cmdId = 'JitterProcessor'

    # ----- CONSTRUCTORS -----

    def __init__(self, ui):
        self.ui = ui
        self.selectedLine = None
        self.sketch = None
        self.startPoint = None
        self.endPoint = None
        self.dominantAxis = None
        self.minSize = None
        self.maxSize = None
        self.recurse = None
        self.handlers = []
        self.previewDisplayed = False
        self.previewRequested = False


    # ----- METHODS -----

    def getSelectedLine(self):
        if self.selectedLine is None:
            # Get the current active selection
            selections = self.ui.activeSelections
            if selections.count != 1:
                self.ui.messageBox('Please select exactly one line in a sketch.')
                return None

            self.selectedLine = selections[0].entity
            
            # Ensure the selected entity is a sketch line
            if not isinstance(self.selectedLine, adsk.fusion.SketchLine):
                self.selectedLine = None
                self.ui.messageBox('Selected entity is not a line. Please select a line in a sketch.')

            self.sketch = self.selectedLine.parentSketch
            
        return self.selectedLine


    def calculateJitterDirection(self, startPoint, endPoint, dominantAxis, cutOutType):
        shapeAxis = 'y' if dominantAxis == 'x' else 'x'
        linePos = (startPoint.__getattribute__(shapeAxis) + endPoint.__getattribute__(shapeAxis)) / 2

        farthestDistance = 0
        farthestPoint = None

        # Iterate through sketch points to find the farthest point along the dominant axis
        for point in self.sketch.sketchPoints:
            if point.isVisible:  # Consider only visible points
                point_pos = point.geometry.__getattribute__(shapeAxis)
                distance = abs(point_pos - linePos)
                if distance > farthestDistance:
                    farthestDistance = distance
                    farthestPoint = point_pos

        # Determine the jitter direction based on the farthest point
        if shapeAxis == 'x':
            if cutOutType == 'concave':
                if farthestPoint >= startPoint.x:
                    direction = Direction.POSITIVE_X
                else:
                    direction = Direction.NEGATIVE_X
            else:
                if farthestPoint >= startPoint.x:
                    direction = Direction.NEGATIVE_X
                else:
                    direction = Direction.POSITIVE_X
        else:
            if cutOutType == 'concave':
                if farthestPoint >= startPoint.y:
                    direction = Direction.POSITIVE_Y
                else:
                    direction = Direction.NEGATIVE_Y
            else:
                if farthestPoint >= startPoint.y:
                    direction = Direction.NEGATIVE_Y
                else:
                    direction = Direction.POSITIVE_Y

        return direction


    def createHemiCircle(self, selectedCurve, startPoint, endPoint, dominantAxis, cutOutSize, direction):
        """
        Adds a hemi-circle cut out on the selectedLine in the given sketch based on the specified parameters.

        Parameters:
            selectedCurve (SketchCurve): The user-selected SketchCurve onto which a new cut will be added.
            startPoint (Point3D): The starting point of the selectedCurve.
            endPoint (Point3D): The ending point of the selectedCurve.
            dominantAxis (str): The axis ('x' or 'y') that determines the direction of expansion.
            cutOutSize (float): The total length of the cut along the dominant axis.
            direction (Direction): The direction to make cut, this must not be along the dominant axis.

        Returns:
            ObjectCollection of SketchCurve objects: Returns the remaining selectedCurve parts after the
            cut has been created and the original selectedCurve modified or trimmed accordingly.
        """

        # Calculate the center point and the size of the cut-out
        centerPoint = adsk.core.Point3D.create((startPoint.x + endPoint.x) / 2, 
                                                (startPoint.y + endPoint.y) / 2, 
                                                (startPoint.z + endPoint.z) / 2)
        radius = round(cutOutSize / 2, 3)

        if direction == Direction.POSITIVE_Y or direction == Direction.NEGATIVE_X:
            startPoint = adsk.core.Point3D.create(centerPoint.x + radius if dominantAxis == 'x' else centerPoint.x, 
                                                    centerPoint.y + radius if dominantAxis == 'y' else centerPoint.y, 
                                                    centerPoint.z)
            endPoint = adsk.core.Point3D.create(centerPoint.x - radius if dominantAxis == 'x' else centerPoint.x, 
                                                    centerPoint.y - radius if dominantAxis == 'y' else centerPoint.y, 
                                                    centerPoint.z)
        else:
            startPoint = adsk.core.Point3D.create(centerPoint.x - radius if dominantAxis == 'x' else centerPoint.x, 
                                                    centerPoint.y - radius if dominantAxis == 'y' else centerPoint.y, 
                                                    centerPoint.z)
            endPoint = adsk.core.Point3D.create(centerPoint.x + radius if dominantAxis == 'x' else centerPoint.x, 
                                                    centerPoint.y + radius if dominantAxis == 'y' else centerPoint.y, 
                                                    centerPoint.z)

        newArc = self.sketch.sketchCurves.sketchArcs.addByCenterStartEnd(centerPoint, startPoint, endPoint)

        resultingCurveParts = self.cleanSelectedCurve(selectedCurve, newArc)

        return resultingCurveParts


    def createRectangle(self, selectedCurve, startPoint, endPoint, dominantAxis, cutOutSize, direction):
        """
        Adds a rectangle cut out on the selectedCurve in the given sketch based on the specified parameters.

        Parameters:
            selectedCurve (SketchCurve): The user-selected SketchCurve onto which a new cut will be added.
            startPoint (Point3D): The starting point of the selectedCurve.
            endPoint (Point3D): The ending point of the selectedCurve.
            dominantAxis (str): The axis ('x' or 'y') that determines the direction of expansion.
            cutOutSize (float): The total length of the cut along the dominant axis.
            direction (Direction): The direction to make cut, this must not be along the dominant axis.

        Returns:
            ObjectCollection of SketchCurve objects: Returns the remaining selectedCurve parts after the
            cut has been created and the original selectedCurve modified or trimmed accordingly.
        """

        # Calculate the center point and the size of the cut-out
        centerPoint = adsk.core.Point3D.create((startPoint.x + endPoint.x) / 2, 
                                                (startPoint.y + endPoint.y) / 2, 
                                                (startPoint.z + endPoint.z) / 2)
        delta = round(cutOutSize / 2, 3)

        # Based on the 'direction', position the new rectangle
        if direction == Direction.POSITIVE_X:
            # Move rectangle rightwards along the X-axis
            rectStart = adsk.core.Point3D.create(centerPoint.x + 2 * delta, centerPoint.y - delta, 0)
            rectEnd = adsk.core.Point3D.create(centerPoint.x, centerPoint.y + delta, 0)
        elif direction == Direction.NEGATIVE_X:
            # Move rectangle leftwards along the X-axis
            rectStart = adsk.core.Point3D.create(centerPoint.x, centerPoint.y - delta, 0)
            rectEnd = adsk.core.Point3D.create(centerPoint.x - 2 * delta, centerPoint.y + delta, 0)
        elif direction == Direction.POSITIVE_Y:
            # Move rectangle upwards along the Y-axis
            rectStart = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y + 2 * delta, 0)
            rectEnd = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y, 0)
        elif direction == Direction.NEGATIVE_Y:
            # Move rectangle downwards along the Y-axis
            rectStart = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y, 0)
            rectEnd = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y - 2 * delta, 0)

        newRect = self.sketch.sketchCurves.sketchLines.addTwoPointRectangle(rectStart, rectEnd)

        # Find intersections and trim the original line
        newRectLine = None
        for line in newRect:
            lineStartPoint = line.startSketchPoint.geometry
            lineEndPoint = line.endSketchPoint.geometry

            # make sure this line coincides with the selected line
            lineDominantAxis = 'x' if abs(lineEndPoint.x - lineStartPoint.x) > abs(lineEndPoint.y - lineStartPoint.y) else 'y'
            if lineDominantAxis == dominantAxis:
                lineNonDominantAxis = 'y' if lineDominantAxis == 'x' else 'x'
                if lineStartPoint.__getattribute__(lineNonDominantAxis) == startPoint.__getattribute__(lineNonDominantAxis):
                    newRectLine = line
                    break

        resultingCurveParts = self.cleanSelectedCurve(selectedCurve, newRectLine)
        newRectLine.deleteMe()

        return resultingCurveParts


    @staticmethod
    def cleanSelectedCurve(originalCurve, newCurve):
        """
        Cleans up the originalCurve by removing the segment defined by newCurve.

        This function splits the originalCurve at the start and end points of newCurve,
        identifies the segment overlapping with newCurve, and deletes it. The function
        returns the remaining segments of the originalCurve as an ObjectCollection.

        Parameters:
            originalCurve (SketchCurve): The curve to be cleaned, containing the segment to remove.
            newCurve (SketchCurve): The curve that defines the segment on the originalCurve to be deleted.

        Returns:
            ObjectCollection of SketchCurve objects: The set of remaining curve segments after the specified segment has been removed.

        Raises:
            RuntimeError: If the overlapping segment cannot be found and removed.
        """

        newCurveStartPoint = newCurve.startSketchPoint.geometry
        newCurveEndPoint = newCurve.endSketchPoint.geometry

        # First, try to split the original curve at the startpoint of the new curve
        potentialNewCurvesSet = originalCurve.split(newCurveStartPoint)

        # Second, we're not sure which of the curves has the end point, so check each and split
        for curve in potentialNewCurvesSet:
            try:
                localNewCurves = curve.split(newCurveEndPoint)
                for curve in localNewCurves:
                    if not curve in potentialNewCurvesSet:
                        potentialNewCurvesSet.add(curve)
                break
            except Exception as e:
                pass
        
        # Third, find the middle curve portion (of the original curve) and delete it
        curveToDelete = None
        for curve in potentialNewCurvesSet:
            curveStartPoint = curve.startSketchPoint.geometry
            curveEndPoint = curve.endSketchPoint.geometry
            if (curveStartPoint.isEqualTo(newCurveStartPoint) or curveStartPoint.isEqualTo(newCurveEndPoint)) \
                    and (curveEndPoint.isEqualTo(newCurveStartPoint) or curveEndPoint.isEqualTo(newCurveEndPoint)):
                curveToDelete = curve
                break
        if curveToDelete is None:
            raise RuntimeError(f"Unable to find middle curve for new curve start {newCurveStartPoint} and end {newCurveEndPoint}.") 
            
        potentialNewCurvesSet.removeByItem(curveToDelete)
        curveToDelete.deleteMe()

        return potentialNewCurvesSet


    def getUserInputSize(self):
        cmdDef = self.ui.commandDefinitions.itemById(self.cmdId)
        if not cmdDef:
            cmdDef = self.ui.commandDefinitions.addButtonDefinition(
                self.cmdId,
                'Edge Jitter',
                'Runs the jitter processor'
            )

        onCommandCreated = self.MyCommandCreatedHandler(self)
        cmdDef.commandCreated.add(onCommandCreated)
        self.handlers.append(onCommandCreated)

        cmdDef.execute()
        adsk.autoTerminate(False)


    def recursiveCut(self, selectedLine, startPoint, endPoint, dominantAxis, minSize, maxSize, recurse):
        # Randomly decide if the cut out is convex or concave
        cutOutType = random.choice(['convex', 'concave'])
        direction = self.calculateJitterDirection(startPoint, endPoint, dominantAxis, cutOutType)
        
        # Randomly decide the type of cut to make
        createFunction = random.choice([self.createRectangle, self.createHemiCircle])
        
        newSelectedCurves = createFunction(selectedLine, startPoint, endPoint, dominantAxis, maxSize, direction)
        
        if recurse:
            for recurseCurve in newSelectedCurves:
                # Make sure the segment to be cut is three times the size of the cut so that the
                # remaining pieces of the segment are proportionate to the cut size
                if recurseCurve.length < (maxSize * 3):
                    continue
                else:
                    recurseCurveStartPoint = recurseCurve.startSketchPoint.geometry
                    recurseCurveEndPoint = recurseCurve.endSketchPoint.geometry
                    self.recursiveCut(recurseCurve, recurseCurveStartPoint, 
                            recurseCurveEndPoint, dominantAxis, minSize, maxSize, recurse)

    def setParams(self, minSize, maxSize, recurse):
        self.setMinSize(minSize)
        self.setMaxSize(maxSize)
        self.setRecurse(recurse)

    def setMinSize(self, minSize):
        self.minSize = minSize
        return self.minSize

    def setMaxSize(self, maxSize):
        self.maxSize = maxSize
        return self.maxSize

    def setRecurse(self, recurse):
        self.recurse = recurse
        return self.recurse

    def callbackFromSizeInput(self):
        if self.minSize is None or self.maxSize is None:
            self.ui.messageBox("Must provide valid, numeric input sizes.")
        
        elif self.minSize <= 0 or self.maxSize >= 100 or self.minSize > self.maxSize:
            self.ui.messageBox("Ensure min is less than max and within the valid range.")

        else:
            self.recursiveCut(self.selectedLine, self.startPoint, self.endPoint, self.dominantAxis, 
                          self.minSize, self.maxSize, self.recurse)
            return True
        
        return False

    def run(self):
        self.selectedLine = self.getSelectedLine()
        if self.selectedLine is None:
            return

        # Get the start and end points of the line
        self.startPoint = self.selectedLine.startSketchPoint.geometry
        self.endPoint = self.selectedLine.endSketchPoint.geometry
        # Determine the direction relative to the dominant axis
        self.dominantAxis = 'x' if abs(self.endPoint.x - self.startPoint.x) > abs(self.endPoint.y - self.startPoint.y) else 'y'
        
        self.getUserInputSize()


    def stop(self):
        try:
            # TODO: Stop properly
            pass
        except:
            if self.parent.ui:
                self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    
    # ----- INNER CLASSES -----
    class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        def notify(self, args: adsk.core.CommandCreatedEventArgs):
            try:
                cmd = adsk.core.Command.cast(args.command)

                cmd.isRepeatable = False

                # inputs
                inputs: adsk.core.CommandInputs = cmd.commandInputs
                
                # inputs.addBoolValueInput('inputRecurseOption', 'Recurse?', True)
                # inputs.addFloatSliderCommandInput('inputFloatSliderMinSize', 'Min Size', 'cm', 0, 100)
                # inputs.addFloatSliderCommandInput('inputFloatSliderMaxSize', 'Max Size', 'cm', 0, 100)
                inputs.addBrowserCommandInput(
                    'browserIptId',
                    '',
                    'EdgeJitterPalette_sizeInput.html',
                    300,
                    100
                )

                # events
                onDestroy = self.parent.MyDestroyHandler(self.parent)
                cmd.destroy.add(onDestroy)
                self.parent.handlers.append(onDestroy)

                onIncomingFromHTML = self.parent.UserInputEventHandler(self.parent)
                cmd.incomingFromHTML.add(onIncomingFromHTML)
                self.parent.handlers.append(onIncomingFromHTML)

                onExecute = self.parent.MyExecuteHandler(self.parent)
                cmd.execute.add(onExecute)
                self.parent.handlers.append(onExecute)

                onExecutePreview = self.parent.MyExecutePreviewHandler(self.parent)
                cmd.executePreview.add(onExecutePreview)
                self.parent.handlers.append(onExecutePreview)

                # # Set up and display the web palette
                # htmlFilePath = 'file:///' + os.path.join(os.path.dirname(__file__), 'EdgeJitterPalette_sizeInput.html').replace('\\', '/')
                # self.palette = self.ui.palettes.itemById('cutSizePalette')
                # if not self.palette:
                #     self.palette = self.ui.palettes.add('cutSizePalette', 'Jitter size configuration', htmlFilePath, True, True, True, 300, 150)
                    
                #     # Attach the event handler
                #     handler = self.UserInputEventHandler() #self.callbackFromSizeInput)
                #     self.palette.incomingFromHTML.add(handler)
                #     self.handlers.append(handler)  # Keep a reference to avoid garbage collection

                    
                #     # Add handler to CloseEvent of the palette.
                #     onClosed = self.UserInputCloseEventHandler()
                #     self.palette.closed.add(onClosed)
                #     self.handlers.append(onClosed)   
                # else:
                #     self.palette.isVisible = True



                # # Decide how big cut out should be
                # (userInput, cancelled) = ui.inputBox("What size for jitter (% or cm)", "Jitter size", "3%")
                # if cancelled:
                #     return None

                # # Trim and remove any spaces
                # userInput = userInput.strip()
                
                # # Check if the input ends with a '%' indicating a percentage
                # if '%' in userInput:
                #     try:
                #         # Remove the '%' and convert to float
                #         percentageValue = float(userInput[:-1])
                #         # Calculate the size as a percentage of the line length
                #         size = round(lineLength * (percentageValue / 100), 3)
                #     except ValueError:
                #         ui.messageBox("Invalid percentage format. Please enter a valid number.")
                #         return None
                # else:
                #     try:
                #         # Extract the numeric part of the input using regular expressions
                #         numericPart = re.findall(r"[-+]?\d*\.\d+|\d+", userInput)
                #         if not numericPart:
                #             ui.messageBox("Please enter a valid numeric value for centimeters.")
                #             return None
                #         # Assume the first found number is the size in millimeters
                #         size = round(float(numericPart[0]), 3)
                #     except ValueError:
                #         ui.messageBox("Invalid centimeter format. Please enter a valid number.")
                #         return None
                
                # # Check if the calculated/entered size is reasonable
                # if size <= 0 or size >= lineLength:
                #     ui.messageBox("Jitter size must be positive and cannot exceed the length of the line.")
                #     return None


            except:
                self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


    class MyExecuteHandler(adsk.core.CommandEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        def notify(self, args):
            try:
                self.parent.callbackFromSizeInput()
            except:
                if self.parent.ui:
                    self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


    class MyExecutePreviewHandler(adsk.core.CommandEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        def notify(self, args):
            """
            This is run upon preview requests. We only build the preview when manually requested
            on button push. Each preview request, re-generates the result from scratch (i.e. 
            may look different on each request).
            """
            if self.parent.previewRequested is True:
                eventArgs = adsk.core.CommandEventArgs.cast(args)
                try:
                    # if a valid callback, mark preview displayed
                    self.parent.previewDisplayed = self.parent.callbackFromSizeInput()
                    eventArgs.isValidResult = self.parent.previewDisplayed
                    self.parent.previewRequested = False
                except:
                    if self.parent.ui:
                        self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


    class UserInputEventHandler(adsk.core.HTMLEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        def notify(self, args):
            if args.action == 'DOMContentLoaded':
                pass
                # args.returnData = "In like flynn"

            elif args.action == 'fieldChanged':
                try:
                    # This method will be called when an HTML event is fired
                    htmlArgs = adsk.core.HTMLEventArgs.cast(args)
                    data = json.loads(htmlArgs.data)

                    if data.get('field') == 'minSize':
                        self.parent.setMinSize(float(data.get('value')))

                    elif data.get('field') == 'maxSize':
                        self.parent.setMaxSize(float(data.get('value')))
                    
                    elif data.get('field') == 'recurse':
                        self.parent.setRecurse(bool(data.get('value')))
                except:
                    self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))     

            elif args.action == 'buttonPushed':
                try:
                    # This method will be called when an HTML event is fired
                    htmlArgs = adsk.core.HTMLEventArgs.cast(args)
                    data = json.loads(htmlArgs.data)
                    
                    if data.get('buttonName') == 'preview':
                        self.parent.previewRequested = True
                        cmd = args.browserCommandInput.parentCommand
                        cmd.doExecutePreview()

                    # args.returnData = f'min: {minSize}; max: {maxSize}'
                except:
                    self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))        

    class MyDestroyHandler(adsk.core.CommandEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
        def notify(self, args: adsk.core.CommandEventArgs):
            adsk.terminate() 

    # Event handler for the palette close event.
    class UserInputCloseEventHandler(adsk.core.UserInterfaceGeneralEventHandler):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        def notify(self, args):
            try:
                self.parent.ui.messageBox('Close button is clicked.') 
            except:
                self.parent.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    ## EVERYONE LOVES THE END OF CLASS

# This is Fusion 360's main method
def run(context):
    global _processor
    ui = adsk.core.Application.get().userInterface
    _processor = JitterProcessor(ui)
    _processor.run()

def stop(context):
    if context.get('IsApplicationClosing', False):
        _processor.stop()
