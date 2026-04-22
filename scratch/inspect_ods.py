from odf import opendocument, table
import io

def inspect_ods(path):
    doc = opendocument.load(path)
    for sheet in doc.spreadsheet.getElementsByType(table.Table):
        print(f"Sheet: {sheet.getAttribute('name')}")
        count = 0
        for row in sheet.getElementsByType(table.TableRow):
            cells = row.getElementsByType(table.TableCell)
            row_vals = []
            for cell in cells:
                from odf.text import P
                p_elements = cell.getElementsByType(P)
                val = " ".join([str(p) for p in p_elements])
                row_vals.append(val)
            if any(v.strip() for v in row_vals):
                print(f"Row {count}: {row_vals[:10]}")
            count += 1
            if count > 30: break

inspect_ods('/home/enyelber/Documentos/area2.ods')
