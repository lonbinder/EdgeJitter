import adsk.core
import adsk.fusion
from constants import Direction
import utils

def create_shape(selected_curve: adsk.fusion.SketchCurve, start_point: adsk.core.Point3D, 
                       end_point: adsk.core.Point3D, dominant_axis, cut_out_size: float, 
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

    center_point = utils.calc_center_point(start_point, end_point)
    arc_width_radius = round(cut_out_size / 2, 3)
    arc_height_radius = utils.random_size(arc_width_radius * .1, arc_width_radius)

    if direction in (Direction.POSITIVE_Y, Direction.NEGATIVE_X):
        arc_start_point = adsk.core.Point3D.create(center_point.x + (arc_width_radius if dominant_axis=='x' else 0),
                                      center_point.y + (arc_width_radius if dominant_axis=='y' else 0),
                                      center_point.z)
        arc_end_point = adsk.core.Point3D.create(center_point.x - (arc_width_radius if dominant_axis=='x' else 0),
                                      center_point.y - (arc_width_radius if dominant_axis=='y' else 0),
                                      center_point.z)
        arc_mid_point = adsk.core.Point3D.create(center_point.x - (arc_height_radius if dominant_axis=='y' else 0),
                                      center_point.y + (arc_height_radius if dominant_axis=='x' else 0),
                                      center_point.z)
    else:
        arc_start_point = adsk.core.Point3D.create(center_point.x - (arc_width_radius if dominant_axis=='x' else 0),
                                      center_point.y - (arc_width_radius if dominant_axis=='y' else 0),
                                      center_point.z)
        arc_end_point = adsk.core.Point3D.create(center_point.x + (arc_width_radius if dominant_axis=='x' else 0),
                                      center_point.y + (arc_width_radius if dominant_axis=='y' else 0),
                                      center_point.z)
        arc_mid_point = adsk.core.Point3D.create(center_point.x + (arc_height_radius if dominant_axis=='y' else 0),
                                      center_point.y - (arc_height_radius if dominant_axis=='x' else 0),
                                      center_point.z)

    sketch = selected_curve.parentSketch
    newArc = sketch.sketchCurves.sketchArcs.addByThreePoints(arc_start_point, arc_mid_point, arc_end_point)
    return utils.clean_selected_curve(selected_curve, newArc)
