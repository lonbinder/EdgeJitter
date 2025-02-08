import traceback
import adsk.core
import jitter_processor

handler_holder = []

class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Handles the command creation event for the JitterProcessor."""
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        global handler_holder

        app = adsk.core.Application.get()
        ui = app.userInterface

        # Verify that a sketch is active.
        if app.activeEditObject.objectType != adsk.fusion.Sketch.classType():
            ui.messageBox('A sketch must be active for this command.')
            return False
        
        try:
            cmd = adsk.core.Command.cast(args.command)
            cmd.isRepeatable = False
            cmd.setDialogMinimumSize(200, 150)

            # inputs
            inputs: adsk.core.CommandInputs = cmd.commandInputs
            inputs.addSelectionInput('inputSelectedCurve', "Selected curve", "Select a single curve (line) to operate on")
            inputs.addBoolValueInput('inputRecurseOption', 'Recurse?', True, '', False)                
            inputs.addDistanceValueCommandInput('inputMinSize', 'Min Size', adsk.core.ValueInput.createByReal(0))
            inputs.addDistanceValueCommandInput('inputMaxSize', 'Max Size', adsk.core.ValueInput.createByReal(0))
            inputs.addBoolValueInput('inputPreview', 'Generate preview', True)

            # Set up event handlers
            on_destroy = MyDestroyHandler()
            cmd.destroy.add(on_destroy)
            handler_holder.append(on_destroy)

            on_execute = MyExecuteHandler()
            cmd.execute.add(on_execute)
            handler_holder.append(on_execute)

            on_execute_preview  = MyExecutePreviewHandler()
            cmd.executePreview.add(on_execute_preview)
            handler_holder.append(on_execute_preview)

            # # Trim and remove any spaces
            # userInput = userInput.strip()
            
            # # Check if the input ends with a '%' indicating a percentage
            # if '%' in userInput:
            #     try:
            #         # Remove the '%' and convert to float
            #         percentageValue = float(userInput[:-1])
            #         # Calculate the size as a percentage of the line length
            #         size = round(lineLength * (percentageValue / 100), 3)
            #     except ValueError:
            #         ui.messageBox("Invalid percentage format. Please enter a valid number.")
            #         return None
            # else:
            #     try:
            #         # Extract the numeric part of the input using regular expressions
            #         numericPart = re.findall(r"[-+]?\d*\.\d+|\d+", userInput)
            #         if not numericPart:
            #             ui.messageBox("Please enter a valid numeric value for centimeters.")
            #             return None
            #         # Assume the first found number is the size in millimeters
            #         size = round(float(numericPart[0]), 3)
            #     except ValueError:
            #         ui.messageBox("Invalid centimeter format. Please enter a valid number.")
            #         return None
            
            # # Check if the calculated/entered size is reasonable
            # if size <= 0 or size >= lineLength:
            #     ui.messageBox("Jitter size must be positive and cannot exceed the length of the line.")
            #     return None
        except:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')

class MyExecuteHandler(adsk.core.CommandEventHandler):
    """Handles the execution of the command."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        event_args = adsk.core.CommandEventArgs.cast(args)
        inputs = event_args.command.commandInputs

        selected_curve = inputs.itemById('inputSelectedCurve').selection(0).entity
        min_size = inputs.itemById('inputMinSize').value
        max_size = inputs.itemById('inputMaxSize').value
        recurse = inputs.itemById('inputRecurseOption').value
        processor = jitter_processor.JitterProcessor(ui, selected_curve, min_size, max_size, recurse)
        try:
            processor.generate()
        except:
            if ui:
                ui.messageBox(f'Failed:\n{traceback.format_exc()}')

class MyExecutePreviewHandler(adsk.core.CommandEventHandler):
    """Handles the preview execution event for the command."""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        """
        This is run upon preview requests. We only build the preview when manually requested
        on button push. Each preview request, re-generates the result from scratch (i.e. 
        may look different on each request).
        """
        ui = adsk.core.Application.get().userInterface

        # According to ADSK F360 docs, each call to preview is wrapped in a transaction and
        # successive calls auto-undo the prior transaction.
        # https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-3922697A-7BF1-4799-9A5B-C8539DF57051#ExecutePreviewEvent

        event_args = adsk.core.CommandEventArgs.cast(args)
        inputs = event_args.command.commandInputs
        generate_preview = inputs.itemById('inputPreview').value

        if generate_preview:
            selected_curve = inputs.itemById('inputSelectedCurve').selection(0).entity
            min_size = inputs.itemById('inputMinSize').value
            max_size = inputs.itemById('inputMaxSize').value
            recurse = inputs.itemById('inputRecurseOption').value
            processor = jitter_processor.JitterProcessor(ui, selected_curve, min_size, max_size, recurse)
            try:
                # if a valid callback, mark preview displayed
                result = processor.generate()
                event_args.isValidResult = result
            except:
                if ui:
                    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))  

class MyDestroyHandler(adsk.core.CommandEventHandler):
    """Handles the command destruction event."""
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.CommandEventArgs):
        adsk.terminate() 
