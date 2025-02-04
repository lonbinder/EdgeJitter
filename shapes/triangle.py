import adsk.core
import adsk.fusion
from constants import Direction
import math
import utils

def create_shape(selected_curve: adsk.fusion.SketchCurve, start_point: adsk.core.Point3D, 
                       end_point: adsk.core.Point3D, dominant_axis, cut_out_size: float, 
                       direction: Direction):
    """
    Adds a triangular cut out on the selectedLine in the given sketch based on the specified parameters.

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
    height = math.sqrt(3) * width_delta # calculate the max height of a proper equilateral triangle
    height = utils.random_size(height * .1, height) # now randomize it between proper and squished

    if direction in (Direction.POSITIVE_Y, Direction.NEGATIVE_X):
        tri_start_point = adsk.core.Point3D.create(center_point.x + (width_delta if dominant_axis=='x' else 0),
                                      center_point.y + (width_delta if dominant_axis=='y' else 0),
                                      center_point.z)
        tri_end_point = adsk.core.Point3D.create(center_point.x - (width_delta if dominant_axis=='x' else 0),
                                      center_point.y - (width_delta if dominant_axis=='y' else 0),
                                      center_point.z)
        tri_mid_point = adsk.core.Point3D.create(center_point.x - (height if dominant_axis=='y' else 0),
                                      center_point.y + (height if dominant_axis=='x' else 0),
                                      center_point.z)
    else:
        tri_start_point = adsk.core.Point3D.create(center_point.x - (width_delta if dominant_axis=='x' else 0),
                                      center_point.y - (width_delta if dominant_axis=='y' else 0),
                                      center_point.z)
        tri_end_point = adsk.core.Point3D.create(center_point.x + (width_delta if dominant_axis=='x' else 0),
                                      center_point.y + (width_delta if dominant_axis=='y' else 0),
                                      center_point.z)
        tri_mid_point = adsk.core.Point3D.create(center_point.x + (height if dominant_axis=='y' else 0),
                                      center_point.y - (height if dominant_axis=='x' else 0),
                                      center_point.z)

    lines = selected_curve.parentSketch.sketchCurves.sketchLines
    line1 = lines.addByTwoPoints(tri_start_point, tri_mid_point)
    line2 = lines.addByTwoPoints(tri_mid_point, tri_end_point)
    return utils.clean_selected_curve_by_points(selected_curve, tri_start_point, tri_end_point)
