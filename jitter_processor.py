import adsk.core, adsk.fusion, traceback, random
from constants import Direction
from utils import random_size
from shapes.shape_factory import random_shape
from handlers import MyCommandCreatedHandler

class JitterProcessor:

    # ----- CONSTANTS -----
    cmdId = 'JitterProcessor'


    # ----- CONSTRUCTORS -----

    def __init__(self, ui):
        self.ui = ui
        self._selected_line = None
        self._sketch = None
        self._start_point = None
        self._end_point = None
        self._dominant_axis = None
        self._min_size = None
        self._max_size = None
        self._recurse = None
        self.handlers = []
        self.preview_displayed = False
        self.preview_requested = False


    # ----- METHODS -----

    def _get_selected_line(self):
        if self._selected_line is None:
            selections = self.ui.activeSelections
            if selections.count != 1:
                self.ui.messageBox('Please select exactly one line in a sketch.')
                return None

            self._selected_line = selections[0].entity
            if not isinstance(self._selected_line, adsk.fusion.SketchLine):
                self._selected_line = None
                self.ui.messageBox('Selected entity is not a line. Please select a line.')
            else:
                self._sketch = self._selected_line.parentSketch
        return self._selected_line


    def _calculate_jitter_direction(self, start_point, end_point, dominant_axis, cut_out_type):
        shape_axis = 'y' if dominant_axis == 'x' else 'x'
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


    def _recursive_cut(self, selected_curve, start_point, end_point, dominant_axis, min_size, max_size,
                       recurse):
        cut_out_type = random.choice(['convex', 'concave'])
        direction = self._calculate_jitter_direction(start_point, end_point, dominant_axis, cut_out_type)
        shape_creator = random_shape() # Randomly decide the type of cut to make
        cut_size = random_size(min_size, max_size)
        new_curves = shape_creator(selected_curve, start_point, end_point, dominant_axis, cut_size, direction)
        if recurse:
            for curve in new_curves:
                # Make sure the remaining pieces of the segment, to the left and right of the cut are
                # proportionate to the cut size.
                if (curve.length / 3) < min_size or curve.length < (max_size * .25):
                    continue
                self._recursive_cut(curve, curve.startSketchPoint.geometry, curve.endSketchPoint.geometry,
                                   dominant_axis, min_size, max_size, recurse)


    def _get_user_input_size(self):
        cmd_def = self.ui.commandDefinitions.itemById(self.cmdId)
        if not cmd_def:
            cmd_def = self.ui.commandDefinitions.addButtonDefinition(
                self.cmdId,
                'Edge Jitter',
                'Runs the jitter processor'
            )

        on_command_created = MyCommandCreatedHandler(self)
        cmd_def.commandCreated.add(on_command_created)
        self.handlers.append(on_command_created)

        cmd_def.execute()
        adsk.autoTerminate(False)

    def callback_from_size_input(self):
        if self._min_size is None or self._max_size is None:
            self.ui.messageBox("Provide valid numeric input sizes.")
            return False
        if self._min_size <= 0 or self._max_size >= 100 or self._min_size > self._max_size:
            self.ui.messageBox("Ensure min < max and within valid range.")
            return False

        self._recursive_cut(self._selected_line, self._start_point, self._end_point, self._dominant_axis,
                            self._min_size, self._max_size, self._recurse)
        return True

    def set_min_size(self, min_size):
        self._min_size = min_size
        return self._min_size

    def set_max_size(self, max_size):
        self._max_size = max_size
        return self._max_size

    def set_recurse(self, recurse):
        self._recurse = recurse
        return self._recurse
    
    def run(self):
        self._selected_line = self._get_selected_line()
        if self._selected_line is None:
            return
        self._start_point = self._selected_line.startSketchPoint.geometry
        self._end_point = self._selected_line.endSketchPoint.geometry
        self._dominant_axis = 'x' if \
            abs(self._end_point.x - self._start_point.x) > abs(self._end_point.y - self._start_point.y) \
                else 'y'
        self._get_user_input_size()

    def stop(self):
        try:
            pass  # Implement proper shutdown.
        except Exception:
            if self.ui:
                self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
