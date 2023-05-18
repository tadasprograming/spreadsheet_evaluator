from spreadsheet_evaluator import *
import pytest


@pytest.mark.parametrize('coordinates, reference', [
    [(0, 0), 'A1'], [(5, 5), 'F6'], [(100, 1), 'B101'],
    [(3, 25), 'Z4']
])
def test_navigate_cell(coordinates, reference):
    assert navigate_cell(reference) == coordinates


@pytest.mark.parametrize('arguments_string, expected_output_list', [
    ['A1', ['A1']],
    ['A1, 1, true, False, 1.5', ['A1', '1', 'true', 'False', '1.5']],
    ['SUM(1, 2), SUM(SUM(1, 2), 2), "Hello"',
     ['SUM(1, 2)', 'SUM(SUM(1, 2), 2)', '"Hello"']],
    ['Hello', '#ERROR: wrong arguments format'],
    ['', '#ERROR: missing arguments in function']
])
def test_get_arguments(arguments_string, expected_output_list):
    assert get_arguments(arguments_string) == expected_output_list


def test_from_file():
    data_file = open('test_data.json', 'r')
    test_json = json.loads(data_file.read())
    sheets_list = test_json['sheets']
    for sheet in range(len(sheets_list)):
        data_sheet = sheets_list[sheet]['data']
        data_sheet = evaluate_sheet(data_sheet)
    data_file_solved = open('test_data_solved.json', 'r')
    json_solved = json.loads(data_file_solved.read())
    sheets_list_solved = json_solved['sheets']
    assert sheets_list == sheets_list_solved


@pytest.mark.parametrize('spreadsheet, evaluated_spreadsheet', [
    [[[-1, +1, 1, 1.111, True, False, 'just_string']],
     [[-1, +1, 1, 1.111, True, False, 'just_string']]], 
    [[['=1', '=-1', '=1.1', '=True', '=false', '=juststring', '==A1']],
     [[1, -1, 1.1, True, False, 'juststring', '=A1']]],
    [[['=SUM()', '=SUM(SUM(A10))', '=SUM(true)', '=MULTIPLY("string")',
       '=DIVIDE(1, 0)', '=DIVIDE(1)', '=GT(1)', '=LT(1, 2)', '=LT(1, true)',
       '=EQ(1, 2, 3)', '=NOT("string", true)', '=IF(false, 1, 2)',
       '=SUMA(1, 2)', '=N1', [], '=IF(true, 1)', '=CONCAT(1, "hello")']],
     [['#ERROR: missing arguments in function',
       '#ERROR: reference to an empty cell',
       '#ERROR: wrong type or number of arguments in SUM',
       '#ERROR: wrong type or number of arguments in MULTIPLY',
       '#ERROR: division by zero',
       '#ERROR: wrong type or number of arguments in DIVIDE',
       '#ERROR: wrong type or number of arguments in GT',
       True, '#ERROR: wrong type or number of arguments in LT',
       '#ERROR: wrong type or number of arguments in EQ',
       '#ERROR: wrong type or number of arguments in NOT',
        2,'#ERROR: unrecognised function',
       '#ERROR: cell refers to itself, infinite loop',
       '#ERROR: unrecognised format of the cell',
       '#ERROR: wrong type or number of arguments in IF',
       '#ERROR: wrong type or arguments in CONCAT']]],
    [[['=SUM(1, B1, SUM(B1, B1, MULTIPLY(10, C1)))', 2,
       '=IF(GT(2, 1), B1, 1)', '=DIVIDE(E1, 10)',
       '=SUM(10, DIVIDE(10, D1))']],
     [[27, 2, 2, '#ERROR: cell refers to itself, infinite loop',
       '#ERROR: cell refers to itself, infinite loop']]]
])
def test_evaluate_sheet(spreadsheet, evaluated_spreadsheet):
    assert evaluate_sheet(spreadsheet) == evaluated_spreadsheet
