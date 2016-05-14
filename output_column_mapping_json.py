import argparse
import libsurveyanalysis as lsa
import json

parser = argparse.ArgumentParser()
parser.add_argument("structure", help="The survey structure file to read from.")
arguments = parser.parse_args()

ss = lsa.SurveyStructure(arguments.structure)

keys = sum([section[1] for section in ss.groups()], [])

output = {}
for key in keys:
    question_data = ss[key]
    if question_data["sub_questions"]:
        if question_data["sub_questions"][0]["code"].lower() == "other":
            output[question_data["code"]] = question_data["label"]
            output[question_data["code"] + "[other]"] = "Other"
        else:
            for subquestion in question_data["sub_questions"]:
                sq_code = question_data["code"] + subquestion["code"]
                output[sq_code] = subquestion["label"]
    else:
        output[question_data["code"]] = question_data["label"]
print(json.dumps(output))
