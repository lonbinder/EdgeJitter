import adsk.core
import adsk.fusion
import traceback

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
import shapes.triangle as triangle
import shapes.shape_factory as shape_factory
import handlers as handlers
import utils as utils
importlib.reload(jitter_processor)
importlib.reload(rectangle)
importlib.reload(hemi_circle)
importlib.reload(triangle)
importlib.reload(shape_factory)
importlib.reload(handlers)
importlib.reload(utils)


# ----- GLOBAL CONSTANTS -----
cmdId = 'JitterProcessor'
handler_holder = []


# ----- METHODS -----

def run(context):
    global cmdId, handler_holder

    """ This is Fusion 360's main method """
    ui = adsk.core.Application.get().userInterface

    cmd_def = ui.commandDefinitions.itemById(cmdId)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            cmdId,
            'Edge Jitter',
            'Runs the jitter processor'
        )
    filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    iconPath = os.path.join(filePath,os.path.join(filePath,"Resources"),"icon")
    cmd_def.resourceFolder = iconPath

    on_command_created = handlers.MyCommandCreatedHandler()
    cmd_def.commandCreated.add(on_command_created)
    handler_holder.append(on_command_created)

    cmd_def.execute()
    adsk.autoTerminate(False)

def stop(context):
    global cmdId

    # if context.get('IsApplicationClosing', False):
    try:
        # Clean up the UI.
        ui = adsk.core.Application.get().userInterface
        cmd_def = ui.commandDefinitions.itemById(cmdId)
        if cmd_def:
            cmd_def.deleteMe()
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
