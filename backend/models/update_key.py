import json
import os

notebook_path = r"D:\emotion-driven-storyteller-main\emotion-driven-storyteller\backend\models\voice_modulation-ultraultimate.ipynb"
new_key = "8b4080f22fa92f19fd8961d22e65e54c8d744cf29f97d0ac0f649d0b0d611fd6"

with open(notebook_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

updated = False
for cell in data['cells']:
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell['source']:
            if 'api_key = "eleven_labs_api_key"' in line:
                new_source.append(f'api_key = "{new_key}"\n')
                updated = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if updated:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Successfully updated API key.")
else:
    print("API key placeholder not found.")
