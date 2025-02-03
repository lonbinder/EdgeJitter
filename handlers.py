import json
import traceback
import adsk.core

class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Handles the command creation event for the JitterProcessor."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = adsk.core.Command.cast(args.command)
            cmd.isRepeatable = False
            cmd.setDialogMinimumSize(200, 150)

            # inputs
            inputs: adsk.core.CommandInputs = cmd.commandInputs
            inputs.addBrowserCommandInput(
                'browserIptId',
                '',
                'EdgeJitterPalette_sizeInput.html',
                200
            )

            # Set up event handlers.
            on_destroy = MyDestroyHandler(self.processor)
            cmd.destroy.add(on_destroy)
            self.processor.handlers.append(on_destroy)

            on_incoming = UserInputEventHandler(self.processor)
            cmd.incomingFromHTML.add(on_incoming)
            self.processor.handlers.append(on_incoming)

            on_execute = MyExecuteHandler(self.processor)
            cmd.execute.add(on_execute)
            self.processor.handlers.append(on_execute)

            on_execute_preview  = MyExecutePreviewHandler(self.processor)
            cmd.executePreview.add(on_execute_preview)
            self.processor.handlers.append(on_execute_preview)

            # # Decide how big cut out should be
            # (userInput, cancelled) = ui.inputBox("What size for jitter (% or cm)", "Jitter size", "3%")
            # if cancelled:
            #     return None

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
            self.processor.ui.messageBox(f'Failed:\n{traceback.format_exc()}')


class MyExecuteHandler(adsk.core.CommandEventHandler):
    """Handles the execution of the command."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def notify(self, args):
        try:
            self.processor.callback_from_size_input()
        except:
            if self.processor.ui:
                self.processor.ui.messageBox(f'Failed:\n{traceback.format_exc()}')


class MyExecutePreviewHandler(adsk.core.CommandEventHandler):
    """Handles the preview execution event for the command."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def notify(self, args):
        """
        This is run upon preview requests. We only build the preview when manually requested
        on button push. Each preview request, re-generates the result from scratch (i.e. 
        may look different on each request).
        """
        if self.processor.preview_requested:
            event_args  = adsk.core.CommandEventArgs.cast(args)
            try:
                # if a valid callback, mark preview displayed
                self.processor.preview_displayed = self.processor.callback_from_size_input()
                event_args.isValidResult = self.processor.preview_displayed
                self.processor.preview_requested  = False
            except:
                if self.processor.ui:
                    self.processor.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class UserInputEventHandler(adsk.core.HTMLEventHandler):
    """Handles HTML events from the command input."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def notify(self, args):
        if args.action == 'DOMContentLoaded':
            pass
            # args.returnData = "In like flynn"

        elif args.action == 'fieldChanged':
            try:
                # This method will be called when an HTML event is fired
                html_args = adsk.core.HTMLEventArgs.cast(args)
                data = json.loads(html_args.data)

                if data.get('field') == 'minSize':
                    self.processor.set_min_size(float(data.get('value')))

                elif data.get('field') == 'maxSize':
                    self.processor.set_max_size(float(data.get('value')))
                
                elif data.get('field') == 'recurse':
                    self.processor.set_recurse(bool(data.get('value')))
            except:
                self.processor.ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))     

        elif args.action == 'buttonPushed':
            try:
                # This method will be called when an HTML event is fired
                html_args = adsk.core.HTMLEventArgs.cast(args)
                data = json.loads(html_args.data)
                
                if data.get('buttonName') == 'preview':
                    self.processor.preview_requested = True
                    cmd = args.browserCommandInput.parentCommand
                    cmd.doExecutePreview()

                # args.returnData = f'min: {minSize}; max: {maxSize}'
            except:
                self.processor.ui.messageBox(f'Failed:\n{traceback.format_exc()}') 

class MyDestroyHandler(adsk.core.CommandEventHandler):
    """Handles the command destruction event."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
    def notify(self, args: adsk.core.CommandEventArgs):
        adsk.terminate() 
