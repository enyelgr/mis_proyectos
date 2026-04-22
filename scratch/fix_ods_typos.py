from odf import opendocument, table, text as odf_text
import re

def fix_area2_ods(path):
    doc = opendocument.load(path)
    changes = 0
    
    replacements = {
        r'10:00pm a 12:00pm': '10:00am a 12:00pm',
        r'2:00am a 5:00pm': '2:00pm a 5:00pm',
    }
    
    for sheet in doc.spreadsheet.getElementsByType(table.Table):
        for cell in sheet.getElementsByType(table.TableCell):
            p_elements = cell.getElementsByType(odf_text.P)
            for p in p_elements:
                for node in p.childNodes:
                    if node.nodeType == node.TEXT_NODE:
                        orig_text = node.data
                        new_text = orig_text
                        for pattern, repl in replacements.items():
                            if re.search(pattern, new_text, re.IGNORECASE):
                                new_text = re.sub(pattern, repl, new_text, flags=re.IGNORECASE)
                        
                        if new_text != orig_text:
                            node.data = new_text
                            changes += 1
                            print(f"Fixed: '{orig_text}' -> '{new_text}'")

    if changes > 0:
        doc.save(path)
        print(f"Success: {changes} typos corrected in {path}")
    else:
        print("No typos found to correct.")

fix_area2_ods('/home/enyelber/Documentos/area2.ods')
