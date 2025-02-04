import adsk.core
import adsk.fusion

# This annoying bit is because Fusion doesn't find our modules otherwise. Ugh
import sys
import os
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

import jitter_processor

# This annoying bit is because Fusion won't reload modules otherwise during dev. Ugh
import importlib
import shapes.rectangle as rectangle
import shapes.hemi_circle as hemi_circle
import constants as constants
import handlers as handlers
importlib.reload(jitter_processor)
importlib.reload(rectangle)
importlib.reload(hemi_circle)
importlib.reload(constants)
importlib.reload(handlers)

_processor = None

def run(context):
    """ This is Fusion 360's main method """
    ui = adsk.core.Application.get().userInterface
    global _processor
    _processor = jitter_processor.JitterProcessor(ui)
    _processor.run()

def stop(context):
    if context.get('IsApplicationClosing', False):
        _processor.stop()
