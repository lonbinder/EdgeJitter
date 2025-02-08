import adsk.core
import adsk.fusion
import random


def clean_selected_curve(original_curve: adsk.fusion.SketchCurve, new_curve: adsk.fusion.SketchCurve):
    """
    Cleans up the original_curve by removing the segment defined by new_curve.

    This function splits the original_curve at the start and end points of new_curve,
    identifies the segment overlapping with new_curve, and deletes it. The function
    returns the remaining segments of the original_curve as an ObjectCollection.

    Parameters:
        original_curve (SketchCurve): The curve to be cleaned, containing the segment to remove.
        new_curve (SketchCurve): The curve that defines the segment on the original_curve to be deleted.

    Returns:
        ObjectCollection of SketchCurve objects: The set of remaining curve segments after the specified segment has been removed.

    Raises:
        RuntimeError: If the overlapping segment cannot be found and removed.
    """
    new_curve_start_point = new_curve.startSketchPoint.geometry
    new_curve_end_point = new_curve.endSketchPoint.geometry
    return clean_selected_curve_by_points(original_curve, new_curve_start_point, new_curve_end_point)

def clean_selected_curve_by_points(original_curve: adsk.fusion.SketchCurve, new_curve_start_point: adsk.core.Point3D,
                                   new_curve_end_point: adsk.core.Point3D):
    """
    Cleans up the original_curve by removing the segment defined by new_curve.

    This function splits the original_curve at the start and end points of new_curve,
    identifies the segment overlapping with new_curve, and deletes it. The function
    returns the remaining segments of the original_curve as an ObjectCollection.

    Parameters:
        original_curve (SketchCurve): The curve to be cleaned, containing the segment to remove.
        new_curve_start_point (Point3D): The start point of the curve(s) that defines the segment along the 
                        original_curve to be deleted.
        new_curve_end_point (Point3D): The end point of the curve(s) that defines the segment along the 
                        original_curve to be deleted.

    Returns:
        ObjectCollection of SketchCurve objects: The set of remaining curve segments after the specified segment has been removed.

    Raises:
        RuntimeError: If the overlapping segment cannot be found and removed.
    """
    trim_mid_point = calc_center_point(new_curve_start_point, new_curve_end_point)
    return original_curve.trim(trim_mid_point)



    # potential_curves = original_curve.split(new_curve_start_point)
    # for curve in potential_curves:
    #     try:
    #         local_curves = curve.split(new_curve_end_point)
    #         for curve in local_curves:
    #             if curve not in potential_curves:
    #                 potential_curves.add(curve)
    #         break
    #     except Exception:
    #         pass

    # curve_to_delete = None
    # for curve in potential_curves:
    #     sp = curve.startSketchPoint.geometry
    #     ep = curve.endSketchPoint.geometry
    #     if ((sp.isEqualTo(new_curve_start_point) or sp.isEqualTo(new_curve_end_point)) and
    #         (ep.isEqualTo(new_curve_start_point) or ep.isEqualTo(new_curve_end_point))):
    #         curve_to_delete = curve
    #         break
    # if curve_to_delete is None:
    #     raise RuntimeError(f"Unable to find middle curve for newCurve points.")
        
    # if curve_to_delete == original_selected_curve:
    #     pass
    # potential_curves.removeByItem(curve_to_delete)
    # curve_to_delete.deleteMe()
    # return potential_curves


def random_size(min_size: float, max_size: float):
    """
    Generate a random size between min_size and max_size, rounded to the nearest 10% increment of min_size.

    Parameters:
        min_size (float): The minimum size.
        max_size (float): The maximum size.

    Returns:
        float: A random size between min_size and max_size, rounded to the nearest increment 
            where the increment is 10% of min_size.
    """
    step = 0.1 * max_size
    value = random.uniform(min_size, max_size)
    return round(value / step) * step


def calc_center_point(start_point: adsk.core.Point3D, end_point: adsk.core.Point3D):
    """
    Calculate the center point between two points.

    Parameters:
        start_point (Point3D): The start point.
        end_point (Point3D): The end point.

    Returns:
        Point3D: The mid-point of the start and end points.
    """
    #TODO Replace this with the built feature to do this in Fusion's API
    return adsk.core.Point3D.create(
        (start_point.x + end_point.x) / 2,
        (start_point.y + end_point.y) / 2,
        (start_point.z + end_point.z) / 2
    )
