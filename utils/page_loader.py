import os
import importlib
import dash

def load_pages(*directories):
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
                    importlib.reload(module)  # Reload to ensure updates are reflected
                    
                    # Ensure the module has the layout attribute and register the page
                    if hasattr(module, "layout"):
                        dash.register_page(module.__name__, path=f"/{module_name}")
                    else:
                        print(f"Warning: {module_name} does not have a layout defined and is not registered as a Dash page.")
                except Exception as e:
                    print(f"Error importing {module_name}: {str(e)}")
