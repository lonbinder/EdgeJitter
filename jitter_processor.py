import adsk.core
import adsk.fusion
from constants import Direction
import random
from utils import random_size
from shapes.shape_factory import random_shape

class JitterProcessor:

    # ----- CONSTRUCTORS -----

    def __init__(self, ui, selected_curve, min_size, max_size=None, recurse=False):
        self.ui = ui
        self._selected_curve = selected_curve
        self._min_size = min_size
        self._max_size = self._min_size if not max_size else max_size
        self._recurse = recurse
        self._sketch = self._selected_curve.parentSketch
        self._dominant_axis = None


    # ----- METHODS -----

    def _calculate_jitter_direction(self, start_point, end_point, cut_out_type):
        shape_axis = 'y' if self._dominant_axis == 'x' else 'x'
        line_pos = (getattr(start_point, shape_axis) + getattr(end_point, shape_axis)) / 2
        farthest_distance = 0
        farthest_point = None
        for point in self._sketch.sketchPoints:
            if point.isVisible:
                pt = point.geometry
                distance = abs(getattr(pt, shape_axis) - line_pos)
                if distance > farthest_distance:
                    farthest_distance = distance
                    farthest_point = getattr(pt, shape_axis)
        if not farthest_point:
            # If no farther point found, consider using the origin
            distance = abs(getattr(self._sketch.origin, shape_axis) - line_pos)
            if distance != 0:
                # Ok, we're using the origin!
                farthest_point = getattr(self._sketch.origin, shape_axis)
            else:
                # No good on origin, because the line is intersecting the origin.
                # We'll just make a "far" point
                farthest_point = adsk.core.Point3D.create(
                        self._sketch.origin.x + 1 if shape_axis == 'x' else 0,
                        self._sketch.origin.y + 1 if shape_axis == 'y' else 0,
                        self._sketch.origin.z)
        
        # Determine direction based on farthest point (simplified logic)
        if shape_axis == 'x':
            if cut_out_type == 'concave':
                return Direction.POSITIVE_X if farthest_point >= start_point.x else Direction.NEGATIVE_X
            else:
                return Direction.NEGATIVE_X if farthest_point >= start_point.x else Direction.POSITIVE_X
        else:
            if cut_out_type == 'concave':
                return Direction.POSITIVE_Y if farthest_point >= start_point.y else Direction.NEGATIVE_Y
            else:
                return Direction.NEGATIVE_Y if farthest_point >= start_point.y else Direction.POSITIVE_Y


    def _recursive_cut(self, selected_curve, start_point, end_point, min_size, max_size,
                       recurse):
        # if not selected_curve.isValid:
        #     return None
        cut_out_type = random.choice(['convex', 'concave'])
        direction = self._calculate_jitter_direction(start_point, end_point, cut_out_type)
        shape_creator = random_shape() # Randomly decide the type of cut to make
        cut_size = random_size(min_size, max_size)
        # Make sure the remaining pieces of the segment, to the left and right of the cut are
        # proportionate to the cut size.
        if not selected_curve or not selected_curve.isValid:
            pass
        if (selected_curve.length * .75) <= cut_size:
            return None
        new_curves = shape_creator(selected_curve, start_point, end_point, self._dominant_axis, cut_size, direction)
        if recurse:
            i = 0
            while i < len(new_curves):
                curve = new_curves.item(i)
                if not curve:
                    pass
                if not curve.isValid:
                    new_curves.removeByIndex(i)
                    continue
                recursed_curves = self._recursive_cut(curve, curve.startSketchPoint.geometry, 
                                                      curve.endSketchPoint.geometry, min_size, max_size, recurse)
                i = i + 1 # work was done, increment the index
                if recursed_curves:
                    for recurse_curve in recursed_curves:
                        if recurse_curve.isValid:
                            new_curves.add(recurse_curve)
        return new_curves
    

    def generate(self):
        if self._selected_curve is None:
            return
        
        if self._min_size is None or self._max_size is None:
            self.ui.messageBox("Provide valid numeric input sizes.")
            return False
        if self._min_size <= 0 or self._max_size >= 100 or self._min_size > self._max_size:
            self.ui.messageBox("Ensure min < max and within valid range.")
            return False
        if self._max_size >= (self._selected_curve.length / 3):
            # This is really important, not just for proportionality, but also because if we cut a segment
            # equal to, or longer than, 1/3rd of the original curve length, it will delete the original curve
            # and the transacation rollback of the preview command does _not_ undo that deletion! It's a bit
            # bananas.
            self.ui.messageBox(f"Max cut must be less than 1/3rd of selected curve length ({self._selected_curve.length} cm).")
            return False

        sc_start_point = self._selected_curve.startSketchPoint.geometry
        sc_end_point = self._selected_curve.endSketchPoint.geometry
        self._dominant_axis = 'x' if \
            abs(sc_end_point.x - sc_start_point.x) > abs(sc_end_point.y - sc_start_point.y) \
                else 'y'
        
        self._recursive_cut(self._selected_curve, sc_start_point, sc_end_point, self._min_size, self._max_size, self._recurse)
        return True
