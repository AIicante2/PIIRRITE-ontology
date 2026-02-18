import os
import re
import sys
import ast
import shutil
import inspect
import subprocess
import numpy as np
from typing import Union, Optional, List
from pathlib import Path
from datetime import datetime

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

def is_number(var) -> bool:
    '''
    Checks wether the passed variable is a number
    
    :param var: the variable to test
    :return: Wether the passed variable is a number
    :rtype: bool
    '''

    try:
        float(var)
        return True
    except ValueError:
        return False

def is_hex_color(var) -> bool:
    '''
    Checks wether the passed variable is an hexadecimal color
    
    :param var: the variable to test
    :return: Wether the passed variable is an hexadecimal color
    :rtype: bool
    '''

    if not isinstance(var, str):
        return False
    
    # Regex pour couleur hex: # suivi de 3 ou 6 caractères hex
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, var))

def is_str_color(var) -> bool:
    '''
    Checks wether the passed variable is a a string representing a color
    
    :param var: the variable to test
    :return: Wether the passed variable is a string representing a color
    :rtype: bool
    '''

    if not isinstance(var, str):
        return False

    possible_colors:list[str] = [
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 
        'black', 'white', 'gray', 'cyan', 'magenta', 'lime', 'navy', 'teal', 
        'olive', 'maroon', 'aqua', 'silver', 'gold', 'beige', 'tan', 'khaki', 
        'ivory', 'coral', 'salmon', 'peach', 'lavender', 'plum', 'violet', 'indigo', 
        'turquoise', 'mint', 'emerald', 'jade', 'forest', 'sage', 'chartreuse', 'crimson', 
        'scarlet', 'burgundy', 'ruby', 'rose', 'fuchsia', 'mauve', 'periwinkle', 'azure', 
        'cobalt', 'sapphire', 'amber', 'bronze', 'copper', 'cream', 'pearl', 'slate'
    ]

    return var in possible_colors

def is_color(var) -> bool:
    '''
    Checks wether the passed variable is a color
    
    :param var: the variable to test
    :return: Wether the passed variable is a color
    :rtype: bool
    '''

    return is_hex_color(var) or is_str_color(var)

def is_date(var, formats=None) -> bool:
    '''
    Checks wether the passed variable is a date
    
    :param var: the variable to test
    :param formats: list of accepted formats (optional)
    :return: Wether var is a date
    :rtype: bool
    '''

    if not isinstance(var, str):
        return False
    
    if formats is None:
        formats = [
            '%Y-%m-%d',      # 2024-12-31
            '%d/%m/%Y',      # 31/12/2024
            '%d-%m-%Y',      # 31-12-2024
            '%Y/%m/%d',      # 2024/12/31
            '%d.%m.%Y',      # 31.12.2024
            '%m/%d/%Y',      # 12/31/2024
        ]
    
    for fmt in formats:
        try:
            datetime.strptime(var, fmt)
            return True
        except ValueError:
            continue
    
    return False

def is_email(var) -> bool:
    '''
    Checks wether the passed variable is an email adress
    
    :param var: The variable to test
    :return: Wether var is an email adress
    :rtype: bool
    '''

    if not isinstance(var, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, var))

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
    # Use ASCII characters for portability
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percent = fraction * 100
    try:
        print(f'\r|{bar}| {percent:.1f}% {message}', end='\r')
    except UnicodeEncodeError:
        # Fallback to ASCII-only
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(f'\r|{bar}| {percent:.1f}% {safe_message}', end='\r')
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


def execute_file(
    file_path: Union[str, Path],
    args: Optional[List[str]] = None,
    use_python: Optional[bool] = None
) -> subprocess.CompletedProcess:
    """
    Execute a file if it has executable permissions.
    
    On Windows, Python scripts are automatically executed with the Python interpreter.
    On Unix-like systems, the file must have executable permissions.
    
    Args:
        file_path: Path to the file to execute (str or Path object)
        args: Optional list of arguments to pass to the script
        use_python: If True, force execution with Python interpreter.
                    If None (default), auto-detect based on file extension.
    
    Returns:
        subprocess.CompletedProcess: The result of the execution
    
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file is not executable (Unix-like systems)
        subprocess.CalledProcessError: If the execution fails
    """
    # Convert to Path object for easier manipulation
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check if it's actually a file (not a directory)
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Determine if we should use Python interpreter
    if use_python is None:
        # Auto-detect: use Python for .py files
        use_python = file_path.suffix.lower() == '.py'
    
    # Build command
    if use_python:
        # Use Python interpreter to execute the script
        cmd = [sys.executable, str(file_path)]
    else:
        # On Unix-like systems, check if file is executable
        if os.name != 'nt' and not os.access(file_path, os.X_OK):
            raise PermissionError(
                f"File is not executable: {file_path}. "
                f"Try running: chmod +x {file_path}"
            )
        cmd = [str(file_path)]
    
    # Add arguments if provided
    if args:
        cmd.extend(args)
    
    # Execute the file
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    return result


def execute_python_module(
    module_path: str,
    args: Optional[List[str]] = None
) -> subprocess.CompletedProcess:
    """
    Execute a Python module using the -m flag.
    
    This is equivalent to running: python -m module.path
    
    Args:
        module_path: Python module path
        args: Optional list of arguments to pass to the module
    
    Returns:
        subprocess.CompletedProcess: The result of the execution
    
    Raises:
        subprocess.CalledProcessError: If the execution fails
    """
    # Build command
    cmd = [sys.executable, '-m', module_path]
    
    # Add arguments if provided
    if args:
        cmd.extend(args)
    
    # Execute the module
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    return result

def copy_file(
    source_path: Union[str, Path],
    destination_path: Union[str, Path],
    overwrite: bool = True
) -> None:
    """
    Copy a file from source to destination.
    
    Args:
        source_path: Path to the source file (str or Path object)
        destination_path: Path to the destination file (str or Path object)
        overwrite: If True, overwrite destination file if it exists.
                   If False, raise an error if destination exists.
                   Default is True.
    
    Raises:
        FileNotFoundError: If the source file does not exist
        FileExistsError: If destination exists and overwrite is False
        IsADirectoryError: If source or destination is a directory
        PermissionError: If lacking permissions to read/write files
    """
    source_path = Path(source_path)
    destination_path = Path(destination_path)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if not source_path.is_file():
        raise IsADirectoryError(f"Source path is not a file: {source_path}")
    
    if destination_path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Destination file already exists: {destination_path}. "
                f"Set overwrite=True to replace it."
            )
        if destination_path.is_dir():
            raise IsADirectoryError(
                f"Destination path is a directory: {destination_path}"
            )
    
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(source_path, destination_path)