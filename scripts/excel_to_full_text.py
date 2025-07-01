import pandas as pd
import sys


def excel_to_full_text(filepath):
    xls = pd.ExcelFile(filepath)
    full_text = ""
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        df = df.fillna("")
        sheet_text = df.to_csv(sep=";", index=False, header=True)
        full_text += f"\n--- HOJA: {sheet_name} ---\n"
        full_text += sheet_text
    return full_text

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python excel_to_full_text.py <archivo_excel> <archivo_salida_txt>")
        sys.exit(1)
    excel_path = sys.argv[1]
    output_path = sys.argv[2]
    text = excel_to_full_text(excel_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Archivo de texto generado: {output_path}")
