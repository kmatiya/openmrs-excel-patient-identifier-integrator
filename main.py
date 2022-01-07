import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import json

emr_username = "openmrs"
emr_pwd = "openmrs"

patient_df = pd.read_excel('./IC3D Study Enrollment Tracker.xlsx', header=0)
complete_patient_url = ""


def get_emr_patient(url, param, username, password):
    return requests.get(url, params=param,
                        auth=HTTPBasicAuth(username=username,
                                           password=password))


def get_emr_uuid(response):
    patient = json.loads(response.text)
    if len(patient["results"]) == 0:
        return ""
    return patient["results"][0]["uuid"]


def remove_trailing_zeros(number):
    manipulandum = str(number)
    trailing_zero_count = len(manipulandum) - len(manipulandum.lstrip('0'))
    first_letter = number[0]
    second_letter = number[1]
    if trailing_zero_count == 4:
        third_letter = number[2]
        fourth_letter = number[3]
        if fourth_letter == '0' and third_letter == '0' and first_letter == '0' and second_letter == '0':
            number = number[4:]
            return number

    if trailing_zero_count == 3:
        third_letter = number[2]
        if third_letter == '0' and first_letter == '0' and second_letter == '0':
            number = number[3:]
            return number

    if trailing_zero_count == 2:
        if first_letter == '0' and second_letter == '0':
            number = number[2:]
            return number

    if trailing_zero_count == 1:
        if first_letter == '0':
            number = number[1:]
            return number
    return number


def format_emr_id(identifier):
    try:
        identifier = identifier.replace("-", " ")
        split_identifier = identifier.split(" ")
        formatted_number = remove_trailing_zeros(split_identifier[1])
        formatted_number = str(formatted_number)
        identifier = identifier.replace(split_identifier[1], formatted_number)
        return identifier
    except:
        return identifier


def get_url(identifier):
    upper_neno_url = "https://neno.pih-emr.org/openmrs//ws/rest/v1/patient"
    lower_neno_url = "http://lisungwi.pih-emr.org:8100/openmrs/ws/rest/v1/patient"
    if identifier.lower().startswith("dam") or identifier.lower().startswith("nsm") or \
            identifier.lower().startswith("nop") or identifier.lower().startswith("lgwe") \
            or identifier.lower().startswith("lwan") or identifier.lower().startswith("mtdn") \
            or identifier.lower().startswith("nno") or identifier.lower().startswith("mgt"):
        return upper_neno_url
    if identifier.lower().startswith("nka") or identifier.lower().startswith("zla") or \
            identifier.lower().startswith("cfga") or identifier.lower().startswith("lsi") \
            or identifier.lower().startswith("mte") or identifier.lower().startswith("mihc"):
        return lower_neno_url
    return False


def get_identifier_location(identifier):
    if identifier.lower().startswith("dam"):
        return '976dcd06-c40e-4e2e-a0de-35a54c7a52ef'
    if identifier.lower().startswith("nsm"):
        return '0d416830-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("nop"):
        return '0d41505c-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("nka"):
        return '0d4169b6-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("zla"):
        return '0d417fd2-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("cfga"):
        return '0d4166a0-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("lsi"):
        return '0d416376-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("mte"):
        return '0d416b3c-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("mihc"):
        return '0d4182e8-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("lgwe"):
        return '0d417e38-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("lwan"):
        return '0d416506-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("mgt"):
        return '0d414eae-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("mtdn"):
        return '0d415200-5ab4-11e0-870c-9f6107fee88e'
    if identifier.lower().startswith("nno"):
        return '0d414ce2-5ab4-11e0-870c-9f6107fee88e'
    return False


if __name__ == '__main__':
    print(patient_df.head())
    for index, row in patient_df.iterrows():
        formatted_emr_id = format_emr_id(str(row["EMR ID"]))
        emr_id = {
            "q": formatted_emr_id,
            "v": "default",
            "limit": "1"
        }
        ic3d_id = {
            "q": str(row["IC3D ID"]),
            "v": "default",
            "limit": "1"
        }
        patient_url = get_url(formatted_emr_id)
        patient_response = get_emr_patient(patient_url, emr_id, emr_username, emr_pwd)
        ic3d_in_emr_response = get_emr_patient(patient_url, ic3d_id, emr_username, emr_pwd)
        if patient_response.status_code == 200 and ic3d_in_emr_response.status_code == 200:
            patient_uuid = get_emr_uuid(patient_response)
            ic3d_uuid = get_emr_uuid(ic3d_in_emr_response)
            if len(patient_uuid) > 0 and len(ic3d_uuid) == 0:
                new_identifier = {
                    "identifier": str(row["IC3D ID"]),
                    "identifierType": "70690634-6522-4552-ba66-43eda7c30217",
                    "location": get_identifier_location(formatted_emr_id),
                    "preferred": False
                }

                complete_patient_url = patient_url + "/" + patient_uuid + "/identifier"
                post_result = requests.post(complete_patient_url, json=new_identifier,
                                            auth=HTTPBasicAuth(username=emr_username, password=emr_pwd))
                print(row["EMR ID"] + ": response from EMR:" + post_result.text)
            else:
                print("Patient with IC3 ID: " + str(row["IC3D ID"]) + " with IC3D Number: " + str(
                    formatted_emr_id) + " already exist in EMR")
