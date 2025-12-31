
from lxml import etree
import argparse
import struct
import numpy as np
import glob
from pathlib import Path

def extract_xml(filename):
    """
    Extract relevant ECG data from a Muse XML file.

    Returns a dictionary with ECG data and metadata.

    Inputs:
    - filename: Path to the Muse XML file.

    Outputs:
    - ECG: Dictionary containing ECG data and metadata.
    """
    def get_int_or_none(path):
        val = root.findtext(path)
        return int(val) if val is not None and val.strip().isdigit() else None

    parser = etree.XMLParser()
    tree = etree.parse(filename, parser)
    root = tree.getroot()

    ECG = {
        'file_path': filename,
        'patient_id': root.findtext('.//PatientID', default='Unknown'),
        'patient_age': get_int_or_none('./PatientDemographics/PatientAge'),
        'patient_gender': root.findtext('./PatientDemographics/Gender', default='Unknown'),
        'patient_race': root.findtext('./PatientDemographics/Race', default='Unknown'),
        'priority': root.findtext('./TestDemographics/Priority', default='Unknown'),
        'location': root.findtext('./TestDemographics/LocationName', default='Unknown'),
        'ecg_date': root.findtext('./TestDemographics/AcquisitionDate', default='Unknown'),
        'acquisition_software_version': root.findtext('./TestDemographics/AcquisitionSoftwareVersion', default='Unknown'),
        'analysis_software_version': root.findtext('./TestDemographics/AnalysisSoftwareVersion', default='Unknown'),
        'overread_lastname': root.findtext('./TestDemographics/OverreaderLastName', default='Unknown'),
        'overread_firstname': root.findtext('./TestDemographics/OverreaderFirstName', default='Unknown'),
        'admit_diagnosis': root.findtext('./Order/AdmitDiagnosis', default='Unknown'),
        'diagnosis_statement': '',
        'original_diagnosis': '',
        'VentricularRate': get_int_or_none('./RestingECGMeasurements/VentricularRate'),
        'AtrialRate': get_int_or_none('./RestingECGMeasurements/AtrialRate'),
        'PRInterval': get_int_or_none('./RestingECGMeasurements/PRInterval'),
        'QRSDuration': get_int_or_none('./RestingECGMeasurements/QRSDuration'),
        'QTInterval': get_int_or_none('./RestingECGMeasurements/QTInterval'),
        'QTCorrected': get_int_or_none('./RestingECGMeasurements/QTCorrected'),
        'PAxis': get_int_or_none('./RestingECGMeasurements/PAxis'),
        'RAxis': get_int_or_none('./RestingECGMeasurements/RAxis'),
        'TAxis': get_int_or_none('./RestingECGMeasurements/TAxis'),
        'QRSCount': get_int_or_none('./RestingECGMeasurements/QRSCount'),
        'Original_VentricularRate': get_int_or_none('./OriginalRestingECGMeasurements/VentricularRate'),
        'Original_AtrialRate': get_int_or_none('./OriginalRestingECGMeasurements/AtrialRate'),
        'Original_PRInterval': get_int_or_none('./OriginalRestingECGMeasurements/PRInterval'),
        'Original_QRSDuration': get_int_or_none('./OriginalRestingECGMeasurements/QRSDuration'),
        'Original_QTInterval': get_int_or_none('./OriginalRestingECGMeasurements/QTInterval'),
        'Original_QTCorrected': get_int_or_none('./OriginalRestingECGMeasurements/QTCorrected'),
        'Original_PAxis': get_int_or_none('./OriginalRestingECGMeasurements/PAxis'),
        'Original_RAxis': get_int_or_none('./OriginalRestingECGMeasurements/RAxis'),
        'Original_TAxis': get_int_or_none('./OriginalRestingECGMeasurements/TAxis'),
        'Original_QRSCount': get_int_or_none('./OriginalRestingECGMeasurements/QRSCount'),
    }

    for diag_statment in root.xpath('./Diagnosis/DiagnosisStatement'):
        if diag_statment.tag.lower() == 'diagnosisstatement':
            ECG['diagnosis_statement'] += diag_statment.find('StmtText').text.strip() + ' '
            try:
                if diag_statment.find('StmtFlag').text.strip() == 'ENDSLINE':
                    ECG['diagnosis_statement'] += '\n'
            except AttributeError:
                pass

    for diag_statement in root.xpath('./OriginalDiagnosis/DiagnosisStatement'):
        if diag_statement.tag.lower() == 'diagnosisstatement':
            ECG['original_diagnosis'] += diag_statement.find('StmtText').text.strip() + ' '
            try:
                if diag_statement.find('StmtFlag').text.strip() == 'ENDSLINE':
                    ECG['original_diagnosis'] += '\n'
            except AttributeError:
                pass


    ECG['diagnosis_statement'] = ECG['diagnosis_statement'].strip() if ECG['diagnosis_statement'] else None
    ECG['original_diagnosis'] = ECG['original_diagnosis'].strip() if ECG['original_diagnosis'] else None

    return ECG

def write_metadata(row_dict, out_path, append=True):
    """
    Write one row of metadata to a TSV file.
    - If append=False (default): overwrite/create file and write header + row.
    - If append=True: create file if missing (write header), otherwise append row only.
    """
    out_path = Path(out_path)
    fieldnames = list(row_dict.keys())

    cleaned = {}
    for k, v in row_dict.items():
        if isinstance(v, str):
            cleaned[k] = v.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
        else:
            cleaned[k] = v

    mode = "a" if append else "w"
    file_exists = out_path.exists()

    with out_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")

        # Write header if overwriting OR appending to a new file
        if (not append) or (append and not file_exists):
            writer.writeheader()

        writer.writerow(cleaned)

def main():
    parser = argparse.ArgumentParser(description="Extract Muse XML metadata and export to TSV.")
    parser.add_argument("xml_file", help="Path to a Muse XML file")
    parser.add_argument("-o", "--out", default="muse_metadata.tsv", help="Output TSV filename (default: muse_metadata.tsv)")
    parser.add_argument("--append", action="store_true", help="Append to TSV (write header only if file doesn't exist)")
    args = parser.parse_args()

    ecg = extract_xml(args.xml_file)
    write_tsv_row(ecg, args.out, append=args.append)
    print(f"Wrote metadata for 1 XML to: {args.out}")

if __name__ == "__main__":
    main()
