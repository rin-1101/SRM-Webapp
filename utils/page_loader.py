import os
import importlib

def load_pages(*directories):
    """Import page modules from directories.

    Dash's built-in `use_pages=True` already registers pages that call
    `dash.register_page()` in their module. This helper should only import
    modules; it must not register them again with inferred paths because that
    can overwrite explicit route constants such as `/dyson-luxe-rewards`.
    """
    base_path = os.path.dirname(__file__)  # Get directory of the script
    for directory in directories:
        full_path = os.path.join(base_path, "..", directory)  # Adjust for relative paths
        print(f"Loading from: {full_path}")
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Directory not found: {full_path}")
        
        module_path = directory.replace("/", ".")  # Convert to module-like path
        for filename in os.listdir(full_path):
            if filename.endswith(".py"):
                module_name = filename[:-3]  # Strip ".py" extension
                try:
                    module = importlib.import_module(f"{module_path}.{module_name}")
                    if not hasattr(module, "layout"):
                        print(f"Warning: {module_name} does not have a layout defined.")
                except Exception as e:
                    print(f"Error importing {module_name}: {str(e)}")
