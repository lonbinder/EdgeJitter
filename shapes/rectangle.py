import adsk.core
import adsk.fusion
from constants import Direction
import utils

def create_shape(selected_curve: adsk.fusion.SketchCurve, start_point: adsk.core.Point3D, 
                       end_point: adsk.core.Point3D, dominant_axis, cut_out_size: float, 
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
    center_point = utils.calc_center_point(start_point, end_point)
    width_delta = round(cut_out_size / 2, 3)
    height_delta = utils.random_size(width_delta * .1, width_delta)

    if direction is Direction.POSITIVE_X:
        rect_start = adsk.core.Point3D.create(center_point.x + 2*height_delta, center_point.y - width_delta, 0)
        rect_end   = adsk.core.Point3D.create(center_point.x, center_point.y + width_delta, 0)
    elif direction is Direction.NEGATIVE_X:
        rect_start = adsk.core.Point3D.create(center_point.x, center_point.y - width_delta, 0)
        rect_end   = adsk.core.Point3D.create(center_point.x - 2*height_delta, center_point.y + width_delta, 0)
    elif direction is Direction.POSITIVE_Y:
        rect_start = adsk.core.Point3D.create(center_point.x - width_delta, center_point.y + 2*height_delta, 0)
        rect_end   = adsk.core.Point3D.create(center_point.x + width_delta, center_point.y, 0)
    elif direction is Direction.NEGATIVE_Y:
        rect_start = adsk.core.Point3D.create(center_point.x - width_delta, center_point.y, 0)
        rect_end   = adsk.core.Point3D.create(center_point.x + width_delta, center_point.y - 2*height_delta, 0)
    else:
        raise ValueError("Invalid direction.")

    sketch = selected_curve.parentSketch
    new_rect = sketch.sketchCurves.sketchLines.addTwoPointRectangle(rect_start, rect_end)
    new_rect_line = None
    for line in new_rect:
        ls = line.startSketchPoint.geometry
        le = line.endSketchPoint.geometry
        axis = 'x' if abs(le.x - ls.x) > abs(le.y - ls.y) else 'y'
        non_dominant_axis = 'y' if axis == 'x' else 'x'
        if axis == dominant_axis and getattr(ls, non_dominant_axis) == getattr(start_point, non_dominant_axis):
            new_rect_line = line
            break

    if new_rect_line is None:
        raise ValueError("Illegal state, can't find newRectLine.")
    
    result = utils.clean_selected_curve(selected_curve, new_rect_line)
    new_rect_line.deleteMe()
    return result
