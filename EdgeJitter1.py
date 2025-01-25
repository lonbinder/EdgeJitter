import adsk.core, adsk.fusion, adsk.cam, traceback
import random
import re  # Import regular expressions
from enum import Enum, auto

class Direction(Enum):
    POSITIVE_X = auto()
    NEGATIVE_X = auto()
    POSITIVE_Y = auto()
    NEGATIVE_Y = auto()

def getSelectedLine(ui):
    # Get the current active selection
    selections = ui.activeSelections
    if selections.count != 1:
        ui.messageBox('Please select exactly one line in a sketch.')
        return None

    selectedLine = selections[0].entity
    
    # Ensure the selected entity is a sketch line
    if not isinstance(selectedLine, adsk.fusion.SketchLine):
        ui.messageBox('Selected entity is not a line. Please select a line in a sketch.')
        return None
    return selectedLine


def calculateJitterDirection(sketch, startPoint, endPoint, dominantAxis, cutOutType):
    shapeAxis = 'y' if dominantAxis == 'x' else 'x'
    linePos = (startPoint.__getattribute__(shapeAxis) + endPoint.__getattribute__(shapeAxis)) / 2

    farthestDistance = 0
    farthestPoint = None

    # Iterate through sketch points to find the farthest point along the dominant axis
    for point in sketch.sketchPoints:
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


def createHemiCircle(sketch, selectedCurve, startPoint, endPoint, dominantAxis, cutOutSize, direction):
    """
    Adds a hemi-circle cut out on the selectedLine in the given sketch based on the specified parameters.

    Parameters:
        sketch (Sketch): The Autodesk Fusion 360 sketch where the cut will be created.
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

    newArc = sketch.sketchCurves.sketchArcs.addByCenterStartEnd(centerPoint, startPoint, endPoint)

    resultingCurveParts = cleanSelectedCurve(selectedCurve, newArc)

    return resultingCurveParts


def createRectangle(sketch, selectedCurve, startPoint, endPoint, dominantAxis, cutOutSize, direction):
    """
    Adds a rectangle cut out on the selectedLine in the given sketch based on the specified parameters.

    Parameters:
        sketch (Sketch): The Autodesk Fusion 360 sketch where the cut will be created.
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

    newRect = sketch.sketchCurves.sketchLines.addTwoPointRectangle(rectStart, rectEnd)

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

    resultingCurveParts = cleanSelectedCurve(selectedCurve, newRectLine)
    newRectLine.deleteMe()

    return resultingCurveParts


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


def getUserInputSize(ui, lineLength):
    # Decide how big cut out should be
    (userInput, cancelled) = ui.inputBox("What size for jitter (% or cm)", "Jitter size", "3%")
    if cancelled:
        return None

    # Trim and remove any spaces
    userInput = userInput.strip()
    
    # Check if the input ends with a '%' indicating a percentage
    if '%' in userInput:
        try:
            # Remove the '%' and convert to float
            percentageValue = float(userInput[:-1])
            # Calculate the size as a percentage of the line length
            size = round(lineLength * (percentageValue / 100), 3)
        except ValueError:
            ui.messageBox("Invalid percentage format. Please enter a valid number.")
            return None
    else:
        try:
            # Extract the numeric part of the input using regular expressions
            numericPart = re.findall(r"[-+]?\d*\.\d+|\d+", userInput)
            if not numericPart:
                ui.messageBox("Please enter a valid numeric value for centimeters.")
                return None
            # Assume the first found number is the size in millimeters
            size = round(float(numericPart[0]), 3)
        except ValueError:
            ui.messageBox("Invalid centimeter format. Please enter a valid number.")
            return None
    
    # Check if the calculated/entered size is reasonable
    if size <= 0 or size >= lineLength:
        ui.messageBox("Jitter size must be positive and cannot exceed the length of the line.")
        return None
    
    return size


def recursiveCut(selectedLine, startPoint, endPoint, dominantAxis, cutOutSize):
    sketch = selectedLine.parentSketch

    # Randomly decide if the cut out is convex or concave
    cutOutType = random.choice(['convex', 'concave'])
    direction = calculateJitterDirection(sketch, startPoint, endPoint, dominantAxis, cutOutType)
    
    # Randomly decide the type of cut to make
    createFunction = random.choice([createRectangle, createHemiCircle])
    
    newSelectedCurves = createFunction(sketch, selectedLine, startPoint, endPoint, dominantAxis, cutOutSize, direction)
    
    for recurseCurve in newSelectedCurves:
        # Make sure the segment to be cut is three times the size of the cut so that the
        # remaining pieces of the segment are proportionate to the cut size
        if recurseCurve.length < (cutOutSize * 3):
            continue
        else:
            recurseCurveStartPoint = recurseCurve.startSketchPoint.geometry
            recurseCurveEndPoint = recurseCurve.endSketchPoint.geometry
            recursiveCut(recurseCurve, recurseCurveStartPoint, 
                    recurseCurveEndPoint, dominantAxis, cutOutSize)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        selectedLine = getSelectedLine(ui)
        if selectedLine is None:
            return

        # Get the start and end points of the line
        startPoint = selectedLine.startSketchPoint.geometry
        endPoint = selectedLine.endSketchPoint.geometry
         # Determine the direction relative to the dominant axis
        dominantAxis = 'x' if abs(endPoint.x - startPoint.x) > abs(endPoint.y - startPoint.y) else 'y'
        
        lineLength = selectedLine.length
        cutOutSize = getUserInputSize(ui, lineLength)
        if cutOutSize is None:
            return  # Handle error or invalid input

        recursiveCut(selectedLine, startPoint, endPoint, dominantAxis, cutOutSize)

        #ui.messageBox(f'Cut-out added: {cutOutType} square at the center of the selected line, heading {direction}.')

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
