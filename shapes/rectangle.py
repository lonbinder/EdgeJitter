import adsk.core
import adsk.fusion
from constants import Direction
from utils import calc_center_point, clean_selected_curve

def create_shape(selectedCurve: adsk.fusion.SketchCurve, startPoint: adsk.core.Point3D, 
                       endPoint: adsk.core.Point3D, dominantAxis, cutOutSize: float, 
                       direction: Direction):
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
    centerPoint = calc_center_point(startPoint, endPoint)
    delta = round(cutOutSize / 2, 3)

    if direction is Direction.POSITIVE_X:
        rectStart = adsk.core.Point3D.create(centerPoint.x + 2*delta, centerPoint.y - delta, 0)
        rectEnd   = adsk.core.Point3D.create(centerPoint.x, centerPoint.y + delta, 0)
    elif direction is Direction.NEGATIVE_X:
        rectStart = adsk.core.Point3D.create(centerPoint.x, centerPoint.y - delta, 0)
        rectEnd   = adsk.core.Point3D.create(centerPoint.x - 2*delta, centerPoint.y + delta, 0)
    elif direction is Direction.POSITIVE_Y:
        rectStart = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y + 2*delta, 0)
        rectEnd   = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y, 0)
    elif direction is Direction.NEGATIVE_Y:
        rectStart = adsk.core.Point3D.create(centerPoint.x - delta, centerPoint.y, 0)
        rectEnd   = adsk.core.Point3D.create(centerPoint.x + delta, centerPoint.y - 2*delta, 0)
    else:
        raise ValueError("Invalid direction.")

    sketch = selectedCurve.parentSketch
    newRect = sketch.sketchCurves.sketchLines.addTwoPointRectangle(rectStart, rectEnd)
    newRectLine = None
    for line in newRect:
        ls = line.startSketchPoint.geometry
        le = line.endSketchPoint.geometry
        axis = 'x' if abs(le.x - ls.x) > abs(le.y - ls.y) else 'y'
        nonDominantAxis = 'y' if axis == 'x' else 'x'
        if axis == dominantAxis and getattr(ls, nonDominantAxis) == getattr(startPoint, nonDominantAxis):
            newRectLine = line
            break

    if newRectLine is None:
        raise ValueError("Illegal state, can't find newRectLine.")
    
    result = clean_selected_curve(selectedCurve, newRectLine)
    newRectLine.deleteMe()
    return result
