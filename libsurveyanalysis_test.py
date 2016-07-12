import unittest
import sqlite3
import libsurveyanalysis as lsa
import json
import argparse

#parser = argparse.ArgumentParser()
#parser.add_argument("database", help="The sqlite database to test with.")
#parser.add_argument("debug_info", help="The debug info file to read from.")
#arguments = parser.parse_args()

db_path = "lsa_test_data.sqlite"

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

class TestKeyAnalyzer(unittest.TestCase):
    def setUp(self):
        """Instantiate the necessary components of a KeyAnalyzer object."""
        self._connection = connection
        self._structure = lsa.SurveyStructure("lw_2016_survey_structure.txt")
        debug_infile = open("lsa_debug_info.json")
        self._debug_info = json.load(debug_infile)
        self._conditions = {}
        self._view = "test_data"
        self._no_null = False
        self._analyzer = lsa.KeyAnalyzer(self._connection, self._structure,
                                         self._conditions, self._view, self._no_null)

    def tearDown(self):
        del(self._analyzer)
    
    def test_analyze_n(self):
        debug_info = self._debug_info[0]
        question_data = debug_info["question_data"]
        test_answers = debug_info["test_answers"]
        cursor = self._connection.cursor()
        test_data = self._analyzer._analyze_N("Age", self._view, question_data,
                                              cursor, False, self._no_null)
        for key in test_data:
            self.assertTrue(test_data[key] == test_answers[key])

    def test_analyze_y(self):
        debug_info = self._debug_info[1]
        question_data = debug_info["question_data"]
        test_answers = debug_info["test_answers"]
        cursor = self._connection.cursor()
        test_data = self._analyzer._analyze_Y("Binary", self._view, question_data,
                                              cursor, False, self._no_null)
        for key in test_answers:
            self.assertTrue(test_answers[key] == test_data[key + "_count"])
            self.assertTrue((test_answers[key] / 500) == test_data[key + "_fraction"])

    def test_analyze_l(self):
        debug_info = self._debug_info[2]
        question_data = debug_info["question_data"]
        test_answers = debug_info["test_answers"]
        cursor = self._connection.cursor()
        test_data = self._analyzer._analyze_L("List", self._view, question_data,
                                              cursor, False, self._no_null)
        for key in test_answers:
            self.assertTrue(test_answers[key] == test_data[key + "_count"])
            self.assertTrue((test_answers[key] / 500) == test_data[key + "_fraction"])
            
if __name__ == "__main__":
    unittest.main()
