import adsk.core
import adsk.fusion
from constants import Direction
from utils import calc_center_point, clean_selected_curve

def create_shape(selectedCurve: adsk.fusion.SketchCurve, startPoint: adsk.core.Point3D, 
                       endPoint: adsk.core.Point3D, dominantAxis, cutOutSize: float, 
                       direction: Direction):
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

    centerPoint = calc_center_point(startPoint, endPoint)
    radius = round(cutOutSize / 2, 3)

    if direction in (Direction.POSITIVE_Y, Direction.NEGATIVE_X):
        sp = adsk.core.Point3D.create(centerPoint.x + (radius if dominantAxis=='x' else 0),
                                      centerPoint.y + (radius if dominantAxis=='y' else 0),
                                      centerPoint.z)
        ep = adsk.core.Point3D.create(centerPoint.x - (radius if dominantAxis=='x' else 0),
                                      centerPoint.y - (radius if dominantAxis=='y' else 0),
                                      centerPoint.z)
    else:
        sp = adsk.core.Point3D.create(centerPoint.x - (radius if dominantAxis=='x' else 0),
                                      centerPoint.y - (radius if dominantAxis=='y' else 0),
                                      centerPoint.z)
        ep = adsk.core.Point3D.create(centerPoint.x + (radius if dominantAxis=='x' else 0),
                                      centerPoint.y + (radius if dominantAxis=='y' else 0),
                                      centerPoint.z)

    sketch = selectedCurve.parentSketch
    newArc = sketch.sketchCurves.sketchArcs.addByCenterStartEnd(centerPoint, sp, ep)
    return clean_selected_curve(selectedCurve, newArc)
