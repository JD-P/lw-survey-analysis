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
    

def generate_x_y_count_rise(results, question_answer):
    """Generate the x and y vectors for the count rise plot given a set of
    [results]."""
    date_indexes = []
    for row in results:
        date_indexes.append((row["id"], row["startdate"]))
    date_indexes.sort()
    unix_timestamps = []
    start_timestamp = timegm(time.strptime(date_indexes[0], "%Y-%m-%d %H:%M:%S"))
    end_timestamp = timegm(time.strptime(date_indexes[-1], "%Y-%m-%d %H:%M:%S"))
    six_hours_seconds = 6 * 60 * 60
    while start_timestamp < end_timestamp:
        unix_timestamps.append(start_timestamp)
        start_timestamp += six_hours_seconds
    indexes = binary_search_dates(unix_timestamps, date_indexes)
    counts = []
    (question, answer) = question_answer.split("|")
    for index in indexes:
        counts.append(tally_answers(results[:index])[question][answer])
    return (list(range(1, len(unix_timestamps) + 1)), counts)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="Path to the survey results CSV file.")
    parser.add_argument("--structure",
                        help="Filepath to the TSV file describing survey structure.")
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
        results.append(row)
    
    question_tallies = tally_answers(results, inreader.fieldnames)
        
    if arguments.brigade:
        brigade_checking.main()
    elif arguments.botcheck and arguments.structure:
        bot_checking.main()
    elif arguments.botcheck:
        raise ValueError("Argument --botcheck requires the survey structure to be "
                         "passed along with it.")
    elif arguments.count_rise:
        (x, y) = generate_x_y_count_rise(results, arguments.count_rise)
        matplotlib.pyplot.xlabel("Hour since start of survey in multiples of six".title())
        matplotlib.pyplot.ylabel("Question response count".title())
        matplotlib.pyplot.scatter(x,y)
        matplotlib.pyplot.show()
    for question in inreader.fieldnames:
        print(question)
        for answer in question_tallies[question]:
            tally = question_tallies[question][answer]
            print(answer +":", (tally / sum(question_tallies[question].values())) * 100)
