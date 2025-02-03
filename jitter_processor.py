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


    def _calculate_jitter_direction(self, startPoint, endPoint, dominantAxis, cutOutType):
        shapeAxis = 'y' if dominantAxis == 'x' else 'x'
        linePos = (getattr(startPoint, shapeAxis) + getattr(endPoint, shapeAxis)) / 2
        farthestDistance = 0
        farthestPoint = None
        for point in self._sketch.sketchPoints:
            if point.isVisible:
                pt = point.geometry
                distance = abs(getattr(pt, shapeAxis) - linePos)
                if distance > farthestDistance:
                    farthestDistance = distance
                    farthestPoint = getattr(pt, shapeAxis)
        # Determine direction based on farthest point (simplified logic)
        if shapeAxis == 'x':
            if cutOutType == 'concave':
                return Direction.POSITIVE_X if farthestPoint >= startPoint.x else Direction.NEGATIVE_X
            else:
                return Direction.NEGATIVE_X if farthestPoint >= startPoint.x else Direction.POSITIVE_X
        else:
            if cutOutType == 'concave':
                return Direction.POSITIVE_Y if farthestPoint >= startPoint.y else Direction.NEGATIVE_Y
            else:
                return Direction.NEGATIVE_Y if farthestPoint >= startPoint.y else Direction.POSITIVE_Y


    def _recursive_cut(self, selectedLine, startPoint, endPoint, dominantAxis, minSize, maxSize, recurse):
        cutOutType = random.choice(['convex', 'concave'])
        direction = self._calculate_jitter_direction(startPoint, endPoint, dominantAxis, cutOutType)
        shapeCreator = random_shape() # Randomly decide the type of cut to make
        cutSize = random_size(minSize, maxSize)
        newCurves = shapeCreator(selectedLine, startPoint, endPoint, dominantAxis, cutSize, direction)
        if recurse:
            for curve in newCurves:
                # Make sure the segment to be cut is three times the size of the cut so that the
                # remaining pieces of the segment are proportionate to the cut size
                if curve.length < (cutSize * 3):
                    continue
                self._recursive_cut(curve, curve.startSketchPoint.geometry, curve.endSketchPoint.geometry,
                                   dominantAxis, minSize, maxSize, recurse)


    def _get_user_input_size(self):
        cmdDef = self.ui.commandDefinitions.itemById(self.cmdId)
        if not cmdDef:
            cmdDef = self.ui.commandDefinitions.addButtonDefinition(
                self.cmdId,
                'Edge Jitter',
                'Runs the jitter processor'
            )

        on_command_created = MyCommandCreatedHandler(self)
        cmdDef.commandCreated.add(on_command_created)
        self.handlers.append(on_command_created)

        cmdDef.execute()
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

    def set_min_size(self, minSize):
        self._min_size = minSize
        return self._min_size

    def set_max_size(self, maxSize):
        self._max_size = maxSize
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
        self._dominant_axis = 'x' if abs(self._end_point.x - self._start_point.x) > abs(self._end_point.y - self._start_point.y) else 'y'
        self._get_user_input_size()

    def stop(self):
        try:
            pass  # Implement proper shutdown.
        except Exception:
            if self.ui:
                self.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
