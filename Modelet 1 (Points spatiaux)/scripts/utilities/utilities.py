import os
import inspect
import subprocess
import ast
import numpy as np

def cls() -> None:
    ''' Cleans the console.
    '''
    os.system('cls' if os.name == 'nt' else 'clear')

def flatten(l:list) -> list:
    ''' Flatten the given list.
    Args:
        l (list) : The list to flatten.
    Returns:
        list : The flattened list'''
    return np.concatenate(l).tolist()

def is_snake_case(s: str) -> bool:
    ''' Checks if a string is in snake_case. If empty, returns False.
    Args:
        s (str) : The input string.
    Returns:
        bool : Wether the string is in snake_case.
    '''
    return s != '' and s.islower() and all(c.isalnum() or c == '_' for c in s)

def snake_to_camel(snake_str: str) -> str:
    ''' Converts a snake_case string to CamelCase.
    Args:
        snake_str (str) : The input string in snake_case.
    Returns:
        str : The converted string in CamelCase.
    '''
    return ''.join(word.title() for word in snake_str.split('_'))

def snake_to_natural(snake_str: str, initial_uppercase:bool = False) -> str:
    ''' Converts a snake_case string to natural syntax.
    Args:
        snake_str (str) : The input string in snake_case.
    Returns:
        str : The converted string in natural syntax.
    '''
    natural_str = ' '.join(word for word in snake_str.split('_'))
    if initial_uppercase:
        return natural_str.capitalize()
    else:
        return natural_str

def is_camel_case(s: str) -> bool:
    ''' Checks if a string is in CamelCase. If empty, returns False.
    Args:
        s (str) : The input string.
    Returns:
        bool : Wether the string is in CamelCase.
    '''
    return s != '' and s[0].isupper() and not '_' in s

def camel_to_snake(camel_str: str) -> str:
    ''' Converts a CamelCase string to snake_case.
    Args:
        camel_str (str) : The input string in CamelCase.
    Returns:
        str : The converted string in snake_case.
    '''
    snake_str = ''
    for i, char in enumerate(camel_str):
        if char.isupper() and i != 0:
            snake_str += '_'
        snake_str += char.lower()
    return snake_str

def display_progress_bar(current: int, total: int, bar_length: int = 50, message: str = 'complete') -> None:
    ''' Displays a progress bar in the console.
    Args:
        current (int) : The current progress value.
        total (int) : The total value for completion.
        bar_length (int) : The length of the progress bar.
        message (str) : A message to display alongside the percentage progression.
    '''
    fraction = current / total
    filled_length = int(bar_length * fraction)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percent = fraction * 100
    print(f'\r|{bar}| {percent:.2f}% {message}', end='\r')
    if current == total:
        print()

def get_current_path() -> str:
    ''' Returns the absolute path to the directory of the script that called this function.
    Returns:
        str : The directory path.
    '''
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError('Unable to get the current frame.')
    try:
        # Remonte d'un cran dans la pile d'appels pour atteindre l'appellent
        caller_frame = frame.f_back
        if caller_frame is None:
            raise RuntimeError('Unable to get the caller frame.')
        caller_path = caller_frame.f_globals['__file__']
        return os.path.dirname(os.path.abspath(caller_path))
    finally:
        del frame

def str_to_best_type(s:str) -> int | float | bool | list | dict | tuple | str:
    ''' Converts a string into the most precise python type.
    If s is '0' or '1', an integer is preferred to a boolean.
    Args:
        s (str) : The string to convert
    Returns:
        int | float | bool | list | dict | tuple | str : The data converted into the most precise python type. 
    '''
    if s.lower() in ['true', 'yes']:
        return True
    elif s.lower() in ['false', 'no']:
        return False

    try:
        return int(s)
    except ValueError:
        pass

    try:
        return float(s)
    except ValueError:
        pass

    try:
        value = ast.literal_eval(s)
        if isinstance(value, (list, dict, tuple)):
            return value
    except (ValueError, SyntaxError):
        pass

    return s

def is_sortable(sequence:list | set):
    ''' Wether the passed sequence is sortable (e.g. only integers).
    Args:
        sequence (list | set) : The sequence to test
    Returns:
        boolean : Wether the sequence is sortable'''
    try:
        sorted(sequence)
        return True
    except TypeError:
        return False

def sort_dict_by_values(dict_to_sort: dict, direction: str = 'asc') -> dict:
    ''' Sorts a dict according to its values.
    If the values are not sortable, returns the passed dict.
    Args:
        dict_to_sort (dict) : The dict to sort
        direction (str) : The sort direction. Supports 'asc' and 'desc'
    Returns:
        dict : The sorted dict
    '''
    if is_sortable(list(dict_to_sort.values())):
        return dict(sorted(dict_to_sort.items(), key = lambda item: item[1], reverse = (direction == 'asc')))
    return dict_to_sort

def run_sparql_query(data_path: str,
                     query_path: str) -> list:
    ''' Runs a SPARQL query using Apache Jena.
    Args:
        data_path (str): The path to the RDF data file.
        query_path (str): The path to the SPARQL query file.
    Returns:
        list: The result of the SPARQL query as a list of strings.
    '''
    cmd = [
        'sparql',
        '--data', data_path,
        '--query', query_path
    ]
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.split('\n')