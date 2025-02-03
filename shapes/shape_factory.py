import pkgutil
import importlib
import random

def _get_shape_creators():
    shape_creators = []
    # Import the current package (i.e., shapes) so we can iterate its modules.
    import shapes  
    for loader, module_name, is_pkg in pkgutil.iter_modules(shapes.__path__):
        # Skip the factory module if present
        if module_name == 'shape_factory':
            continue
        module = importlib.import_module(f'shapes.{module_name}')
        # Each shape module should define a standard creation function, e.g. "create_shape"
        if hasattr(module, 'create_shape'):
            shape_creators.append(module.create_shape)
    return shape_creators

def random_shape():
    """
    Dynamically discovers and returns a random shape creation function from the shapes package.

    This function searches the modules in the 'shapes' package for functions named 'create_shape',
    which are expected to implement shape creation logic. It then selects one of these functions at random
    and returns it.

    Returns:
        Callable: A shape creation function with the signature:
                  create_shape(sketch, selectedCurve, startPoint, endPoint, dominantAxis, cutOutSize, direction)

    Raises:
        RuntimeError: If no shape creation functions are found in the shapes package.
    """
    creators = _get_shape_creators()
    if not creators:
        raise RuntimeError("No shape creation functions found in shapes package.")
    return random.choice(creators)
