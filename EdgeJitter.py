import adsk.core
import adsk.fusion

# This annoying bit is because Fusion doesn't find our modules otherwise. Ugh
import sys
import os
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from jitter_processor import JitterProcessor

_processor = None

def run(context):
    """ This is Fusion 360's main method """
    ui = adsk.core.Application.get().userInterface
    global _processor
    _processor = JitterProcessor(ui)
    _processor.run()

def stop(context):
    if context.get('IsApplicationClosing', False):
        _processor.stop()
