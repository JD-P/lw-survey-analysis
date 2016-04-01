import sys
import csv
import argparse
import time
import calendar
import random
import matplotlib.pyplot
try:
    import bot_checking
except:
    print("Bot checking module not included with your distribution, the "
          "--botcheck option will fail if used.")
try:
    import brigade_checking
except:
    print("Brigade checking module not included with your distribution, the "
          "--brigade option will fail if used.")
timegm = calendar.timegm

def sample_results(results, size):
    """Sample [size] rows from the [results]."""
    sample = []
    generator = random.SystemRandom()
    random_selection = set()
    while len(random_selection) < size:
        choice = generator.randrange(0, len(results))
        random_selection.add(choice)
    for index in random_selection:
        sample.append(results[index])
    return sample

def tally_answers(results, fieldnames):
    """Tally the answers to questions in results."""
    question_tallies = dict().fromkeys(fieldnames)
    for question in question_tallies:
        question_tallies[question] = dict()
    for row in results:
        for question in row:
            if row[question].strip() and row[question].strip() != "N/A":
                if row[question].strip() not in question_tallies[question]:
                    question_tallies[question][row[question].strip()] = 1
                else:
                    question_tallies[question][row[question].strip()] += 1
    return question_tallies

def detect_write_ins(results, threshold):
    """Detect those questions which are write ins by measuring the number of 
    possible answers which appear in the survey results above [threshold]."""
    question_answers = {}
    write_ins = set()
    for row in results:
        for question in row:
            if question in question_answers:
                if row[question] in question_answers[question]:
                    pass
                else:
                    question_answers[question].add(row[question])
                    if len(question_answers[question]) >= threshold:
                        write_ins.add(question)
            else:
                question_answers[question] = set()
    return list(write_ins)

def detect_num_responses(fieldnames, write_ins):
    """Detect those questions which have a distinct number of possible answers
    and how many by detecting the write ins and subtracting them and then 
    counting the number of responses observed in the survey results."""
    non_write_ins = set(fieldnames[:])
    for field in fieldnames:
        try:
            if "[other]" in field:
                non_write_ins.remove(field)
            elif field in write_ins:
                non_write_ins.remove(field)
        except KeyError:
            continue
    return non_write_ins
    
def import_survey_structure(filepath):
    """Take the tab separated values file at [filepath] and import them into a 
    representation of the survey as follows:

    {"question":[answer1, answer2, answer3], ...}"""
    infile = open(filepath)
    structure_raw = infile.read()
    structure = structure_raw.split("\n")
    fieldnames = structure[0]
    questions = {}
    for row in structure[1:]:
        values = row.split("\t")
        values = [x for x in values if x]
        if values[0].lower() == "q":
            question = values[2]
            questions[question] = []
        elif values[0].lower() == "a":
            questions[question].append(values[3])
    return questions

def binary_search_dates(unix_timestamps, date_indexes):
    """Determine the index of the results for each unix_timestamp beyond which
    all further values will be greater."""
    unix_timestamps.sort()
    date_indexes.sort()
    indexes = []
    if len(unix_timestamps) > 1:
        mid = round(len(unix_timestamps) / 2)
        return (binary_search_dates(unix_timestamps[:mid], date_indexes) +
                binary_search_dates(unix_timestamps[mid:], date_indexes))
    elif len(unix_timestamps) == 1:
        return bsearch_basecase(unix_timestamps, date_indexes)

def bsearch_basecase(unix_timestamps, date_indexes):
    mid = round(len(date_indexes) / 2)
    if len(date_indexes) == 1:
        return [date_indexes[0][0]]
    elif unix_timestamps[0] == date_indexes[mid][1]:
        return [date_indexes[mid][0]]
    elif unix_timestamps[0] > date_indexes[mid][1]:
        bsearch_basecase(unix_timestamps, date_indexes[mid:])
    else:
        bsearch_basecase(unix_timestamps, date_indexes[:mid])
    return "???"

def generate_x_y_count_rise(results, question_answer):
    """Generate the x and y vectors for the count rise plot given a set of
    [results]."""
    date_indexes = []
    for row in results:
        date_indexes.append((int(row["id"]),
                             timegm(time.strptime(row["startdate"],
                                                  "%Y-%m-%d %H:%M:%S"))))
    date_indexes.sort()
    unix_timestamps = []
    start_timestamp = date_indexes[0][1]
    end_timestamp = date_indexes[-1][1]
    six_hours_seconds = 6 * 60 * 60
    while start_timestamp < end_timestamp:
        unix_timestamps.append(start_timestamp)
        start_timestamp += six_hours_seconds
    indexes = binary_search_dates(unix_timestamps, date_indexes)
    counts = []
    (question, answer) = question_answer.split("|")
    results.sort(key=lambda item:item["id"])
    print(indexes)
    for index in indexes:
        counts.append(tally_answers(results[:index])[question][answer])
    return (list(range(1, len(unix_timestamps) + 1)), counts)

def filter_rm_section_time(row):
    """Filter out the time it took to complete a given section from the internal
    survey results for a given row."""
    row_copy = row.copy()
    for question in row.keys():
        try:
            if question + "Time" in row_copy:
                row_copy.pop(question + "Time")
            elif question[-4:] == "Time":
                row_copy.pop(question)
            elif "groupTime" in question:
                row_copy.pop(question)
        except KeyError:
            continue
    return row_copy

def filter_rm_non_public(row):
    """Filter out anyone who did not opt into the public release."""
    if row["GeneralPrivacy"] == "Yes":
        return row
    else:
        return False

def filter_mod_ipaddrs(results):
    """Exchange each ip address in the survey results data with a unique number."""
    ipaddrs = {}
    id_ = 0
    for row in results:
        if row["ipaddr"] in ipaddrs:
            continue
        else:
            ipaddrs[row["ipaddr"]] = id_
            id_ += 1
    for row in results:
        row["ipaddr"] = ipaddrs[row["ipaddr"]]
    return results

def filter_mod_datestamps(row):
    """Remove the timestamp portion of the datestamps. THIS SHOULD ONLY BE USED
    FOR PARTNER RELEASE, THE PUBLIC RELEASE SHOULD STRIP THESE ENTIRELY AND USE
    filter_rm_datestamps."""
    del(row["datestamp"])
    row["submitdate"] = row["submitdate"].split(" ")[0]
    row["startdate"] = row["startdate"].split(" ")[0]
    return row

def filter_rm_misc(row):
    """Remove miscellaneous things such as row ID and lastpage."""
    del(row["interviewtime"])
    del(row["lastpage"])
    del(row["refurl"])
    del(row["id"])
    return row

def filter_rm_emailaddr(row):
    """Remove the mailing list from the survey results. THIS IS PROBABLY THE 
    BIGGEST POSSIBLE RELEASE SCREW UP, THESE MUST BE REMOVED FROM THE PUBLIC 
    RELEASE."""
    del(row["EmailAddress"])
    return row

def filter_rm_coppa(row):
    """Remove data entries for survey respondents who reported themselves as being
    under 13 years of age to comply with COPPA."""
    if not row["Age"] or row["Age"] == "N/A":
        return row
    elif float(row["Age"]) > 12:
        return row
    else:
        return False

def strip_data_for_partner_release(results):
    """Strip the survey data so that it is suitable for release to trusted 
    partners. This is almost the same thing as the public release, but includes
    just a few more potentially identifying pieces of information such as the
    date the survey was started and the date it was submitted, a unique number
    representing an anonymized IP address, etc."""
    stripped = []
    results = filter_mod_ipaddrs(results)
    for row in results:
        if filter_rm_non_public(row):
            stripped_row = filter_rm_section_time(row)
            stripped_row = filter_mod_datestamps(stripped_row)
            stripped_row = filter_rm_misc(stripped_row)
            stripped_row = filter_rm_emailaddr(stripped_row)
            stripped_row = filter_rm_coppa(stripped_row)
            stripped.append(stripped_row)
        else:
            continue
    return stripped
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to the survey results CSV file.")
    parser.add_argument("--structure",
                        help="Filepath to the TSV file describing survey structure.")
    parser.add_argument("-o", "--output", help="Filepath to write output to.")
    parser.add_argument("-p", "--public",
                        help="Only output entries that have opted into the "
                        "public dataset.")
    parser.add_argument("--partner-release", dest="partner_release", type=int,
                        help="Release a sample of size n appropriate for " +
                        "release to trusted partners.")
    parser.add_argument("-b", "--brigade", action="store_true", help="Do brigading analysis.")
    parser.add_argument("--botcheck", action="store_true", help="Analyze possible bot replies.")
    parser.add_argument("--count-rise", dest="count_rise",
                        help="Generate a scatter plot of the response count for a "
                        "given question in six hour increments.")
    parser.add_argument("-t", action="store_true", help="Test procedures.")
    arguments = parser.parse_args()
    
    infile = open(arguments.filepath, newline='')
    inreader = csv.DictReader(infile)
    results = []

    for row in inreader:
        if arguments.public:
            if row["GeneralPrivacy"] == "Yes":
                results.append(row)
            else:
                continue
        else:
            results.append(row)
    
    question_tallies = tally_answers(results, inreader.fieldnames)
        
    if arguments.brigade:
        brigade_checking.main()
    elif arguments.partner_release:
        if arguments.partner_release > len(results):
            raise ValueError("Currently only" + str(len(results)) +
                             " in dataset. Must be between this number and zero.")
        sample = sample_results(results, arguments.partner_release)
        stripped = strip_data_for_partner_release(sample)
        if arguments.output:
            outfile = open(arguments.output, mode="w", newline='')
        else:
            outfile = sys.stdout
        fieldnames = []
        for field in inreader.fieldnames:
            if field in stripped[0]:
                fieldnames.append(field)
        outwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
        outwriter.writeheader()
        for row in stripped:
            outwriter.writerow(row)
        quit()
    elif arguments.botcheck and arguments.structure:
        bot_checking.main()
    elif arguments.botcheck:
        raise ValueError("Argument --botcheck requires the survey structure to be "
                         + "passed along with it.")
    elif arguments.count_rise:
        (x, y) = generate_x_y_count_rise(results, arguments.count_rise)
        print(x, y)
        matplotlib.pyplot.xlabel("Hour since start of survey in multiples of six".title())
        matplotlib.pyplot.ylabel("Question response count".title())
        matplotlib.pyplot.scatter(x,y)
        matplotlib.pyplot.show()
        quit()
    for question in inreader.fieldnames:
        print(question)
        for answer in question_tallies[question]:
            tally = question_tallies[question][answer]
            print(answer +":", (tally / sum(question_tallies[question].values())) * 100)
