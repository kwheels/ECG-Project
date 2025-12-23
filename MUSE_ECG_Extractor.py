from lxml import etree
from matplotlib import pyplot as plt
import base64
import struct
import numpy as np
import glob
from pathlib import Path


def decode_waveform(b64_data, scale=4.88):
    """
    Decode base64-encoded waveform data from Muse XML files.
    Inputs:
    - b64_data: Base64-encoded string of waveform data.
    - scale: Scaling factor to convert raw data to microvolts.
    Outputs:
    - Numpy array of decoded waveform samples in microvolts.
    """

    try:
        # Decode base64 to binary
        binary_data = base64.b64decode(b64_data)
        num_samples = len(binary_data) // 2

        # Unpack little-endian signed 16-bit integers
        samples = struct.unpack('<' + 'h' * num_samples, binary_data[:num_samples*2])

        # Scale to microvolts
        return np.array(samples) * scale
    except Exception as e:
        return f"[Error decoding waveform: {e}]"


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
        'diagnosis_statement': '',
        'original_diagnosis': '',
        'leads': {
            'I': np.array([]),
            'II': np.array([]),
            'V1': np.array([]),
            'V2': np.array([]),
            'V3': np.array([]),
            'V4': np.array([]),
            'V5': np.array([]),
            'V6': np.array([]),
        },
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


def get_lead_data(filename):
    """
    Extract lead waveform data from a Muse XML file.

    Inputs:
    - filename: Path to the Muse XML file.

    Outputs:
    - leads: Dictionary with lead names as keys and numpy arrays of waveform data as values.
    """

    parser = etree.XMLParser()
    tree = etree.parse(filename, parser)
    root = tree.getroot()
    leads = {
        'I': np.array([]),
        'II': np.array([]),
        'III': np.array([]),
        'aVR': np.array([]),
        'aVL': np.array([]),
        'aVF': np.array([]),
        'V1': np.array([]),
        'V2': np.array([]),
        'V3': np.array([]),
        'V4': np.array([]),
        'V5': np.array([]),
        'V6': np.array([]),
    }
    for waveform in root.xpath('.//Waveform'):
        waveform_type = waveform.find('WaveformType').text.lower()
        if waveform_type != 'rhythm':
            continue
        pass

        for lead_data in waveform.xpath('.//LeadData'): # Waveform to get median or whatever
            lead_id_elem = lead_data.find('LeadID')
            waveform_elem = lead_data.find('WaveFormData')

            lead_id = lead_id_elem.text.strip().upper() if lead_id_elem is not None else '[Unknown LeadID]'
            waveform_text = waveform_elem.text.strip() if waveform_elem is not None else ''

            if lead_id in leads.keys():
                # print(f"\n--- Lead: {lead_id} ---")
                scale_elem = lead_data.find('LeadAmplitudeUnitsPerBit')
                scale = float(scale_elem.text.strip()) if scale_elem is not None else 1.0
                decoded = decode_waveform(waveform_text, scale=scale)
                # print(f"Decoded {len(decoded)} samples:")
                leads[lead_id] = np.array(decoded)
                # print(decoded[:20], "... (first 20 samples)")
            else:
                print("No waveform data found.")

    leads["III"] = leads["II"] - leads["I"]
    leads["aVR"] = -(leads["I"] + leads["II"]) / 2
    leads["aVL"] = leads["I"] - leads["II"] / 2
    leads["aVF"] = leads["II"] - leads["I"] / 2

    return leads


def plot_ecgs(filename):
    """
    Plot ECG lead waveforms from a Muse XML file.

    Inputs:
    - filename: Path to the Muse XML file.

    Outputs:
    - None (displays plots).
    """

    ecg = get_lead_data(filename)
    leads = ["aVF", "V2", "V5"]
    num_leads = len(leads)
    fig, axs = plt.subplots(num_leads, 1, figsize=(10, 2 * num_leads), sharex=True)
    for i, lead in enumerate(leads):
        axs[i].plot(ecg[lead])
        axs[i].set_title(f'Lead {lead}')
        axs[i].set_ylabel('Amplitude (µV)')
        axs[i].grid(True)
    axs[-1].set_xlabel('Samples')
    plt.tight_layout()
    plt.show()
