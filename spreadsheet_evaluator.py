import requests
import json
import re


'''navigate_cell(address) - takes a string with a cell reference (e.g. 'A1')
and returns the cell coordinates y, x (y - rows, x - columns).
Only wokrs with [A-Z][0-9]+ format. It obtains x by using unicode indexes.'''


def navigate_cell(address):
    x = ord(address[:1])-65
    y = int(address[1:])-1
    return y, x


'''get_arguments(arg_string) - takes a string with the list of arguments
(e.g. '1, A1, SUM(1, A1)') and returns a list of strings with the arguments
separated (e.g. ['1', 'A1', 'SUM(1, A1)']). Regular expression operations
(re module) are used in this function. The function recognizes patterns at the
beginning of the string, chops them, and collects them into a list
(excluding ', ').'''


def get_arguments(args_string):
    if args_string == '':
        return '#ERROR: missing arguments in function'

    patterns = [
        r', ',                 # ', '
        r'[+-]?\d*\.?\d+',     # any integer or float, could have + or - sign
        r'\b(true|false)\b',   # true or false
        r'\b(True|False)\b',   # True or False
        r'\".*?\"',            # text in quotation marks
        r'[A-Z][0-9]+',        # cell index
        # function with nested functions
        # (P.S. must be matching number of parenthesis)
        r'[A-Z]+\((?:[^()]|\((?:[^()]+)\))*\)'
    ]

    args_list = []
    i = 0
    while i <= len(patterns)-1 and args_string != '':
        try:
            patterns[i] = re.compile(patterns[i])
            # .group() will cause AttributeError if match wasn't found
            # P.S. match checks only beggining of the string
            arg = patterns[i].match(args_string).group()
            args_string = args_string.replace(arg, '', 1)
            if arg != ', ':
                args_list.append(arg)
            i = 0
        except AttributeError:
            i += 1
    else:
        if args_string == '':
            return args_list
        else:
            return '#ERROR: wrong arguments format'


'''format_arguments(arguments) - takes a list of separated strings of arguments
and turns them to the corresponding format. If the argument contains a
reference index or a function, it will be solved until it is an int, float,
bool, or string (without functions or references). The solve_cell() function
will be used to solve references. To accomplish this, we will place a reference
argument into the current cell we are working with; in this case, we will not
lose the feature of avoiding infinite loops (read solve_cell for more info).'''


def format_arguments(args):
    for i in range(len(args)):
        try:
            args[i] = int(args[i])
        except ValueError:
            try:
                args[i] = float(args[i])
            except ValueError:
                if args[i].lower() == 'true':
                    args[i] = True
                elif args[i].lower() == 'false':
                    args[i] = False
                elif re.search(r'^[A-Z][0-9]+$', args[i]):
                    # to adapt to solve_cell() functonality we have to add '='
                    data[y][x] = '=' + args[i]
                    args[i] = solve_cell(y, x)
                    # since args[i] can be int, float or bool we have to
                    # check if it's string before [:6], so we don't get error
                    if type(args[i]) == str and \
                       args[i][:6] == '#ERROR':
                        return args[i]
                elif re.search(r'^[A-Z]+\(', args[i]) and \
                        args[i][-1] == ')':
                    # we have to cut ')' at the end before giving the string
                    # to solve_function
                    args[i] = solve_function(args[i][:-1])
                    if type(args[i]) == str and \
                       args[i][:6] == '#ERROR':
                        return args[i]
                elif args[i][0] == '"' and args[i][-1] == '"':
                    args[i] = args[i][1:-1]
                else:
                    continue
    return args


'''solve_function(func_string) - takes string of function and return
compiled value. Arguments string is without '=' at the beginning and
without ')' at the end (e.g. 'SUM(1, A1, SUM(1, 2)'). Function separates
string into function name (e.g. SUM) and function arguments string
(e.g. 1, A1, SUM(1, 2)). Arguments string is formatted by get_arguments()
and format_arguments(). Afterwards, arguments are used in the block
corresponding to the function name, picked by switch argument statement.
In every case before compiling function, it is checked if the number and
format of arguments is correct.'''


def solve_function(func_string):
    # spliting string into function name and arguments(spliting by first '(')
    first_bracket = func_string.find('(')
    func_name = func_string[:first_bracket]
    func_args_string = func_string[(first_bracket+1):]
    func_args_list = get_arguments(func_args_string)
    if func_args_list[:6] == '#ERROR':
        return func_args_list
    args = format_arguments(func_args_list)
    if args[:6] == '#ERROR':
        return args
    match func_name:
        case 'SUM':
            if any(type(arg) is not int
                   and type(arg) is not float for arg in args):
                return '#ERROR: wrong type or number of arguments in SUM'
            return sum(args)
        case 'MULTIPLY':
            if any(type(arg) is not int
                   and type(arg) is not float for arg in args):
                return '#ERROR: wrong type or number of arguments in MULTIPLY'
            result = 1
            for arg in args:
                result *= arg
            return result
        case 'DIVIDE':
            if len(args) != 2 or any(type(arg) is not int and
                                     type(arg) is not float for arg in args):
                return '#ERROR: wrong type or number of arguments in DIVIDE'
            try:
                return round(args[0] / args[1], 7)
            except ZeroDivisionError:
                return '#ERROR: division by zero'
        case 'GT':
            if len(args) != 2 or any(type(arg) is not int and
                                     type(arg) is not float for arg in args):
                return '#ERROR: wrong type or number of arguments in GT'
            return args[0] > args[1]
        case 'LT':
            if len(args) != 2 or any(type(arg) is not int and
                                     type(arg) is not float for arg in args):
                return '#ERROR: wrong type or number of arguments in LT'
            return args[0] < args[1]
        case 'EQ':
            if len(args) != 2:
                return '#ERROR: wrong type or number of arguments in EQ'
            return args[0] == args[1]
        case 'NOT':
            if len(args) != 1 or type(args[0]) != bool:
                return '#ERROR: wrong type or number of arguments in NOT'
            return not (args[0])
        case 'AND':
            if len(args) < 1 or any(type(arg) is not bool for arg in args):
                return '#ERROR: wrong type or number of arguments in AND'
            return all(arg is True for arg in args)
        case 'OR':
            if len(args) < 1 or any(type(arg) is not bool for arg in args):
                return '#ERROR: wrong type or number of arguments in OR'
            return any(arg is True for arg in args)
        case 'IF':
            if len(args) != 3 or type(args[0]) != bool:
                return '#ERROR: wrong type or number of arguments in IF'
            return args[1] if args[0] else args[2]
        case 'CONCAT':
            if any(type(arg) is not str for arg in args):
                return '#ERROR: wrong type or arguments in CONCAT'
            result = ''
            for arg in args:
                if arg[0] == '"' and arg[-1] == '"':
                    result += arg[1:-1]
                else:
                    result += arg
            return result

        case _:
            return '#ERROR: unrecognised function'


'''solve_cell(y, x) - takes coordinates (y - row, x - collum) of the cell in
a data matrix (spreadsheet) and returns compiled value. Solve_cell will also
be used to solve all references within the cell (this is a recursive function).
Also solve_function can use solve_cell to solve references in arguments.
This allows us to check if the cell is referring itself. It will accomplish
this by setting data[y][x] = 'working' and checking the value of data[y][x]
every time a cell is referred to. Data[y][x] will also be used to store
references that must be solved, whereas the cell will store the original cell
value. If another cell is solved during cell solving, it will be saved.'''


def solve_cell(y, x):
    try:
        cell = data[y][x]
    except IndexError:
        return '#ERROR: reference to an empty cell'

    if cell == 'working':
        return '#ERROR: cell refers to itself, infinite loop'
    else:
        data[y][x] = 'working'

    if type(cell) in [int, float, bool]:
        return cell
    if type(cell) != str:
        return '#ERROR: unrecognised format of the cell'
    elif cell[0] != '=':
        return cell
    else:
        # regular expresion for references
        if re.search(r'^=[A-Z][0-9]+$', cell):
            coord = navigate_cell(cell[1:])  # cut '='
            solved_cell = solve_cell(coord[0], coord[1])
            if type(solved_cell) == str and \
               solved_cell[:6] == '#ERROR':
                return solved_cell
            else:
                data[coord[0]][coord[1]] = solved_cell
                return solved_cell
        # regular expresion for functions
        elif re.search(r'^=[A-Z]+\(', cell) and cell[-1] == ')':
            # '=' and ')' is cuted before giving it to solve_function
            cell = solve_function(cell[1:-1])
            return cell
        # property value (e.g. '=41')
        else:
            # since formar_arguments returns list, adding [0]
            return format_arguments([cell[1:]])[0]


'''evaluate_sheet(data_fix) - takes one single spreadsheet, compiles it and
returns it.'''


def evaluate_sheet(data_fix):
    global y, x, data
    data = data_fix
    for y in range(len(data_fix)):
        for x in range(len(data_fix[y])):
            data[y][x] = solve_cell(y, x)
    return data


if __name__ == '__main__':
    # GET
    get_url =\
     'https://www.wix.com/_serverless/hiring-task-spreadsheet-evaluator/sheets?tag=nested_structures'
    response_get = requests.get(get_url)
    response_get_json = response_get.json()
    # COMPILE
    sheets_list = response_get_json['sheets']

    for sheet in range(len(sheets_list)):
        data_sheet = sheets_list[sheet]['data']
        #print(data_sheet)
        data_sheet = evaluate_sheet(data_sheet)
    # POST
    post_url = response_get_json['submissionUrl']
    post_json = {"email": "tadas222@gmail.com", "results": sheets_list}
    response_post = requests.post(post_url, json=post_json)
    print(response_post)
    print(response_post.text)
