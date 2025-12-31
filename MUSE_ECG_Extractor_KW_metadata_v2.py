
from lxml import etree
import argparse
import csv
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

FIELDNAMES = [
    "file_path",
    "patient_id",
    "patient_age",
    "patient_gender",
    "patient_race",
    "priority",
    "location",
    "ecg_date",
    "acquisition_software_version",
    "analysis_software_version",
    "overread_lastname",
    "overread_firstname",
    "admit_diagnosis",
    "diagnosis_statement",
    "original_diagnosis",
    "VentricularRate",
    "AtrialRate",
    "PRInterval",
    "QRSDuration",
    "QTInterval",
    "QTCorrected",
    "PAxis",
    "RAxis",
    "TAxis",
    "QRSCount",
    "Original_VentricularRate",
    "Original_AtrialRate",
    "Original_PRInterval",
    "Original_QRSDuration",
    "Original_QTInterval",
    "Original_QTCorrected",
    "Original_PAxis",
    "Original_RAxis",
    "Original_TAxis",
    "Original_QRSCount",
]

def iter_xml_files(inputs):
    """
    Yield XML files from a list of input paths.
    - If a path is a file: yield it if it ends with .xml
    - If a path is a directory: recursively yield *.xml
    """
    for p in inputs:
        path = Path(p)
        if path.is_file() and path.suffix.lower() == ".xml":
            yield path
        elif path.is_dir():
            yield from path.rglob("*.xml")

def clean_row_for_tsv(row_dict):
    """
    Normalize strings so TSV stays one record per line.
    Converts newlines to literal '\\n'.
    """
    cleaned = {}
    for k in FIELDNAMES:
        v = row_dict.get(k, None)
        if isinstance(v, str):
            cleaned[k] = v.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
        else:
            cleaned[k] = v
    return cleaned


def write_metadata_batch(xml_paths, out_tsv, append=False, progress_every=1000):
    """
    Stream extraction results into a TSV (one row per XML).
    Opens the output file once (fast).
    Writes header if needed.
    """
    out_tsv = Path(out_tsv)
    file_exists = out_tsv.exists()

    mode = "a" if append else "w"
    with out_tsv.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES,
            delimiter="\t",
            extrasaction="ignore"
        )

        # Write header only if we're overwriting OR appending to a new file
        if (not append) or (append and not file_exists):
            writer.writeheader()

        n = 0
        for xml_file in xml_paths:
            try:
                ecg = extract_xml(str(xml_file))
                writer.writerow(clean_row_for_tsv(ecg))
                n += 1
                if progress_every and n % progress_every == 0:
                    print(f"Processed {n:,} files... (latest: {xml_file})")
            except Exception as e:
                # Keep going; log failures to stderr-friendly output
                print(f"[WARN] Failed on {xml_file}: {e}")

    print(f"Done. Wrote {n:,} rows to {out_tsv}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract Muse XML metadata and export to a single TSV."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="One or more XML files or directories (directories searched recursively for *.xml)"
    )
    parser.add_argument(
        "-o", "--out",
        default="muse_metadata_all.tsv",
        help="Output TSV filename"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing TSV (header written only if file does not exist)"
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1000,
        help="Print progress every N files (0 to disable)"
    )
    args = parser.parse_args()

    xml_iter = iter_xml_files(args.inputs)
    write_metadata_batch(
        xml_paths=xml_iter,
        out_tsv=args.out,
        append=args.append,
        progress_every=args.progress_every
    )

if __name__ == "__main__":
    main()
