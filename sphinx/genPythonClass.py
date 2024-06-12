import re

PLACEHOLDERS = {
    '_state_': 'SomeStateClass',
    '_shape_': 'SomeShapeClass',
    '_material_': 'SomeMaterialClass'
}
# Define placeholder classes (this can be replaced with actual imports if they exist)
PLACEHOLDER_DEFINITIONS = """
class SomeStateClass:
    \"\"\"abstract state class\"\"\"
    pass

class SomeShapeClass:
    \"\"\"abstract shape class\"\"\"
    pass

class SomeMaterialClass:
    \"\"\"abstract material class\"\"\"
    pass
"""

def replace_latex_and_cite(docstring):
    """Replaces $...$ with :math:`...` and \cite{} with :cite:`...`"""
    docstring = re.sub(r'\$(.+?)\$', r':math:`\1`', docstring)
    docstring = re.sub(r'\\cite\{(.+?)\}', r':cite:`\1`', docstring)
    print(docstring)
    return docstring

def parse_class_definitions(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    imports = []
    classes = {}
    current_class = None
    current_attributes = []

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        if stripped_line.startswith('import') or stripped_line.startswith('from'):
            imports.append(stripped_line)
            continue

        if not line.startswith(' '):  # New class definition
            if current_class:
                classes[current_class] = current_attributes

            parts = stripped_line.split(':')
            class_name = parts[0].strip()
            class_doc = parts[1].strip()
            if '(' in class_name:
                class_name, base_classes = class_name.split('(')
                class_name = class_name.strip()
                base_classes = base_classes.rstrip(')').strip()
                for placeholder, replacement in PLACEHOLDERS.items():
                    base_classes = base_classes.replace(placeholder, replacement)
            else:
                base_classes = None
            if '(' in class_name:
                class_name, base_classes = class_name.split('(')
                class_name = class_name.strip()
                base_classes = base_classes.rstrip(')').strip()
            current_class = (class_name, replace_latex_and_cite(class_doc), base_classes)
            current_attributes = []
        else:
            attr_parts = stripped_line.split('#')
            attr_definition = attr_parts[0].strip()
            attr_doc = attr_parts[1].strip() if len(attr_parts) > 1 else ""
            # Replace placeholders in attributes
            for placeholder, replacement in PLACEHOLDERS.items():
                attr_definition = attr_definition.replace(placeholder, replacement)
                attr_doc = attr_doc.replace(placeholder, replacement)
            # Replace $...$ with :math:`...`
            attr_doc = re.sub(r'\$(.+?)\$', r':math:`\1`', attr_doc)
            # Replace \cite{...} with :cite:`...`
            attr_doc = re.sub(r'\\cite\{(.+?)\}', r':cite:`\1`', attr_doc)
            current_attributes.append((attr_definition, attr_doc))

    if current_class:
        classes[current_class] = current_attributes

    return imports, classes

def generate_mymodule_py(imports, classes, output_file, with_preamble):
    with open(output_file, 'w') as file:
        if with_preamble:
            # import base types first, since they are not repeated in each input file
            file.write('from vector3 import *\n')
            # Write imports and placeholder definitions
            file.write(PLACEHOLDER_DEFINITIONS)
            file.write('\n')
        
        # these imports must be in the input txt directly
        for imp in imports:
            file.write(f'{imp}\n')
        file.write('\n')
        
        for (class_name, class_doc, base_classes), attributes in classes.items():
            if base_classes:
                file.write(f'class {class_name}({base_classes}):\n')
            else:
                file.write(f'class {class_name}:\n')

            docstring = f'    """{class_doc}"""\n'
            file.write(docstring)

            for attr_definition, attr_doc in attributes:
                attr_name = attr_definition.split(':')[0].strip()
                if '=' in attr_definition:
                    default_value = attr_definition.split('=')[1].strip()
                else:
                    default_value = 'None'
                attr_type = attr_definition.split(':')[1].split('=')[0].strip()
                file.write(f'    {attr_name}: {attr_type} = {default_value}\n')
                file.write(f'    """{attr_doc}"""\n')

            if True: # define __init__()
                file.write('\n    def __init__(self):\n')
                if base_classes:
                    base_classes_list = base_classes.split(',')
                    for base_class in base_classes_list:
                        file.write(f'        super({base_class.strip()}, self).__init__()\n')

                for attr_definition, _ in attributes:
                    attr_name = attr_definition.split(':')[0].strip()
                    if '=' in attr_definition:
                        default_value = attr_definition.split('=')[1].strip()
                    else:
                        default_value = 'None'
                    file.write(f'        self.{attr_name} = {default_value}\n')

            file.write('\n')

# Example usage:
import os
build_dir = '../build/py'
if not os.path.exists(build_dir):
    os.makedirs(build_dir)

imports, bodies = parse_class_definitions('body.txt')
generate_mymodule_py(imports, bodies, os.path.join(build_dir, 'body.py'),True)

imports, interactions = parse_class_definitions('interaction.txt')
generate_mymodule_py(imports, interactions, os.path.join(build_dir, 'interaction.py'),True)

imports, interactions = parse_class_definitions('model.txt')
generate_mymodule_py(imports, interactions, os.path.join(build_dir, 'model.py'),False)
