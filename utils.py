import adsk.core
import adsk.fusion
import random


def clean_selected_curve(originalCurve: adsk.fusion.SketchCurve, newCurve: adsk.fusion.SketchCurve):
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

    potentialCurves = originalCurve.split(newCurveStartPoint)
    for curve in potentialCurves:
        try:
            localCurves = curve.split(newCurveEndPoint)
            for c in localCurves:
                if c not in potentialCurves:
                    potentialCurves.add(c)
            break
        except Exception:
            pass

    curveToDelete = None
    for curve in potentialCurves:
        sp = curve.startSketchPoint.geometry
        ep = curve.endSketchPoint.geometry
        if ((sp.isEqualTo(newCurveStartPoint) or sp.isEqualTo(newCurveEndPoint)) and
            (ep.isEqualTo(newCurveStartPoint) or ep.isEqualTo(newCurveEndPoint))):
            curveToDelete = curve
            break
    if curveToDelete is None:
        raise RuntimeError(f"Unable to find middle curve for newCurve points.")
        
    potentialCurves.removeByItem(curveToDelete)
    curveToDelete.deleteMe()
    return potentialCurves


def random_size(minSize: float, maxSize: float):
    """
    Generate a random size between minSize and maxSize, rounded to the nearest 10% increment of minSize.

    Parameters:
        minSize (float): The minimum size.
        maxSize (float): The maximum size.

    Returns:
        float: A random size between minSize and maxSize, rounded to the nearest increment 
            where the increment is 10% of minSize.
    """
    step = 0.1 * minSize
    value = random.uniform(minSize, maxSize)
    return round(value / step) * step


def calc_center_point(startPoint: adsk.core.Point3D, endPoint: adsk.core.Point3D):
    """
    Calculate the center point between two points.

    Parameters:
        minSize (float): The minimum size.
        maxSize (float): The maximum size.

    Returns:
        float: A random size between minSize and maxSize, rounded to the nearest increment 
            where the increment is 10% of minSize.
    """
    #TODO Replace this with the built feature to do this in Fusion's API
    return adsk.core.Point3D.create(
        (startPoint.x + endPoint.x) / 2,
        (startPoint.y + endPoint.y) / 2,
        (startPoint.z + endPoint.z) / 2
    )
