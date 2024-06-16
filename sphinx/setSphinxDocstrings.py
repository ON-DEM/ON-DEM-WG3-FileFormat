# replace latex' \cite{} and $...$ by sphinx :cite: and :math:

import re

def replace_latex_and_cite(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Replace $...$ with :math:`...`
    content = re.sub(r'\$(.+?)\$', r':math:`\1`', content)
    
    # Replace \cite{...} with :cite:`...`
    content = re.sub(r'\\cite\{(.+?)\}', r':cite:`\1`', content)

    # Write the modified content to the output file
    with open(file_path, 'w') as file:
        file.write(content)

replace_latex_and_cite('body.py')
replace_latex_and_cite('interaction.py')
replace_latex_and_cite('model.py')
