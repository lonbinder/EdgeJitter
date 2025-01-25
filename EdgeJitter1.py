import adsk.core, adsk.fusion, adsk.cam, traceback
import random
import re  # Import regular expressions
from enum import Enum, auto

class Direction(Enum):
    POSITIVE_X = auto()
    NEGATIVE_X = auto()
    POSITIVE_Y = auto()
    NEGATIVE_Y = auto()

def get_selected_line(ui):
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


def calculate_jitter_direction(sketch, startPoint, endPoint, dominantAxis, cutOutType):
    shapeAxis = 'y' if dominantAxis == 'x' else 'x'
    line_pos = (startPoint.__getattribute__(shapeAxis) + endPoint.__getattribute__(shapeAxis)) / 2

    farthest_distance = 0
    farthest_point = None

    # Iterate through sketch points to find the farthest point along the dominant axis
    for point in sketch.sketchPoints:
        if point.isVisible:  # Consider only visible points
            point_pos = point.geometry.__getattribute__(shapeAxis)
            distance = abs(point_pos - line_pos)
            if distance > farthest_distance:
                farthest_distance = distance
                farthest_point = point_pos

    # Determine the jitter direction based on the farthest point
    if shapeAxis == 'x':
        if cutOutType == 'concave':
            if farthest_point >= startPoint.x:
                direction = Direction.POSITIVE_X
            else:
                direction = Direction.NEGATIVE_X
        else:
            if farthest_point >= startPoint.x:
                direction = Direction.NEGATIVE_X
            else:
                direction = Direction.POSITIVE_X
    else:
        if cutOutType == 'concave':
            if farthest_point >= startPoint.y:
                direction = Direction.POSITIVE_Y
            else:
                direction = Direction.NEGATIVE_Y
        else:
            if farthest_point >= startPoint.y:
                direction = Direction.NEGATIVE_Y
            else:
                direction = Direction.POSITIVE_Y

    return direction


def createHemiCircle(sketch, selectedLine, startPoint, endPoint, dominantAxis, cutOutSize, direction):
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

    resultingCurveParts = cleanSelectedLine(selectedLine, newArc)

    return resultingCurveParts


def createRectangle(sketch, selectedLine, startPoint, endPoint, dominantAxis, cutOutSize, direction):
    # Calculate the center point and the size of the cut-out
    centerPoint = adsk.core.Point3D.create((startPoint.x + endPoint.x) / 2, 
                                            (startPoint.y + endPoint.y) / 2, 
                                            (startPoint.z + endPoint.z) / 2)
    delta = round(cutOutSize / 2, 3)

    # Based on the 'direction', position the new rectangle
    if direction == Direction.POSITIVE_X:
        # Move rectangle rightwards along the X-axis
        rect_start = adsk.core.Point3D.create(centerPoint.x + 2 * delta, centerPoint.y - delta, 0)
        rect_end = adsk.core.Point3D.create(centerPoint.x, centerPoint.y + delta, 0)
    elif direction == Direction.NEGATIVE_X:
        # Move rectangle leftwards along the X-axis
        rect_start = adsk.core.Point3D.create(centerPoint.x, centerPoint.y - delta, 0)
        rect_end = adsk.core.Point3D.create(centerPoint.x - 2 * delta, centerPoint.y + delta, 0)
    elif direction == Direction.POSITIVE_Y:
        # Move rectangle upwards along the Y-axis
        rect_start = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y + 2 * delta, 0)
        rect_end = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y, 0)
    elif direction == Direction.NEGATIVE_Y:
        # Move rectangle downwards along the Y-axis
        rect_start = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y, 0)
        rect_end = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y - 2 * delta, 0)

    newRect = sketch.sketchCurves.sketchLines.addTwoPointRectangle(rect_start, rect_end)

    # Find intersections and trim the original line
    newRectLine = None
    for line in newRect:
        line_start_point = line.startSketchPoint.geometry
        line_end_point = line.endSketchPoint.geometry

        # make sure this line coincides with the selected line
        line_dominant_axis = 'x' if abs(line_end_point.x - line_start_point.x) > abs(line_end_point.y - line_start_point.y) else 'y'
        if line_dominant_axis == dominantAxis:
            line_non_dom_axis = 'y' if line_dominant_axis == 'x' else 'x'
            if line_start_point.__getattribute__(line_non_dom_axis) == startPoint.__getattribute__(line_non_dom_axis):
                newRectLine = line
                break

    resultingCurveParts = cleanSelectedLine(selectedLine, newRectLine)
    newRectLine.deleteMe()

    return resultingCurveParts


def cleanSelectedLine(originalCurve, newCurve):
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
    (user_input, cancelled) = ui.inputBox("What size for jitter (% or cm)", "Jitter size", "3%")
    if cancelled:
        return None

    # Trim and remove any spaces
    user_input = user_input.strip()
    
    # Check if the input ends with a '%' indicating a percentage
    if '%' in user_input:
        try:
            # Remove the '%' and convert to float
            percentage_value = float(user_input[:-1])
            # Calculate the size as a percentage of the line length
            size = round(lineLength * (percentage_value / 100), 3)
        except ValueError:
            ui.messageBox("Invalid percentage format. Please enter a valid number.")
            return None
    else:
        try:
            # Extract the numeric part of the input using regular expressions
            numeric_part = re.findall(r"[-+]?\d*\.\d+|\d+", user_input)
            if not numeric_part:
                ui.messageBox("Please enter a valid numeric value for centimeters.")
                return None
            # Assume the first found number is the size in millimeters
            size = round(float(numeric_part[0]), 3)
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
    direction = calculate_jitter_direction(sketch, startPoint, endPoint, dominantAxis, cutOutType)
    
    # Randomly decide the type of cut to make
    createFunction = random.choice([createRectangle, createHemiCircle])
    
    newSelectedCurves = createFunction(sketch, selectedLine, startPoint, endPoint, 
            dominantAxis, cutOutSize, direction)
    
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

        selectedLine = get_selected_line(ui)
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
