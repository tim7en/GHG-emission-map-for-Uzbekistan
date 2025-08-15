#!/usr/bin/env python3
"""
Unicode Fixer Script for GHG Emissions Project

This scrip    '\u2103': 'C',                 # C degree Celsius
    '\u2109': 'F',                 # F degree Fahrenheit
    
    # Additional Unicode characters found in testing
    '\U0001f3ed': 'FACTORY:',      # 🏭 factory
    '\U0001f9ea': 'TEST_TUBE:',    # 🧪 test tube  
    '\U0001f4d6': 'BOOK:',         # 📖 open book
    '\U0001f441': 'EYE:',          # 👁 eye
    '\U0001f4c1': 'FOLDER:',       # 📁 file folder
    '\U0001f4c2': 'FILES:',        # 📂 open file folder
}inds and fixes Unicode characters that cause encoding issues
in Windows terminals by replacing them with ASCII equivalents.

Author: GHG Analysis Team
Date: August 15, 2025
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime

# Unicode characters that cause issues and their ASCII replacements
UNICODE_REPLACEMENTS = {
    # Checkmarks and status symbols
    '\u2705': 'SUCCESS:',          # SUCCESS: heavy check mark
    '\u2713': 'OK:',               # OK: check mark
    '\u2714': 'DONE:',             # DONE: heavy check mark
    '\u2611': '[CHECKED]',         # [CHECKED] ballot box with check
    '\u2612': '[UNCHECKED]',       # [UNCHECKED] ballot box with X
    
    # Warning and error symbols
    '\u26a0': 'WARNING:',          # WARNING: warning sign
    '\u26a0\ufe0f': 'WARNING:',    # WARNING: warning sign with variation selector
    '\u274c': 'ERROR:',            # ERROR: cross mark
    '\u274e': 'ERROR:',            # ERROR: negative squared cross mark
    '\u2717': 'FAILED:',           # FAILED: ballot X
    '\u2718': 'FAILED:',           # FAILED: heavy ballot X
    
    # Progress and action symbols
    '\U0001f680': 'STARTING:',     # STARTING: rocket
    '\U0001f6e0': 'TOOLS:',        # TOOLS: hammer and wrench
    '\U0001f527': 'SETTINGS:',     # SETTINGS: wrench
    '\U0001f4ca': 'CHART:',        # CHART: bar chart
    '\U0001f4c8': 'TRENDING:',     # TRENDING: chart with upwards trend
    '\U0001f4c9': 'DECLINING:',    # DECLINING: chart with downwards trend
    '\U0001f4cb': 'CLIPBOARD:',    # CLIPBOARD: clipboard
    '\U0001f4dd': 'MEMO:',         # MEMO: memo
    '\U0001f4be': 'STORAGE:',      # STORAGE: floppy disk
    '\U0001f310': 'GLOBE:',        # GLOBE: globe with meridians
    '\U0001f30d': 'EARTH:',        # EARTH: earth globe Europe-Africa
    '\U0001f30e': 'EARTH:',        # EARTH: earth globe Americas
    '\U0001f30f': 'EARTH:',        # EARTH: earth globe Asia-Australia
    
    # Science and analysis symbols
    '\U0001f52c': 'MICROSCOPE:',   # MICROSCOPE: microscope
    '\U0001f3af': 'TARGET:',       # TARGET: direct hit
    '\U0001f4a8': 'EMISSION:',     # EMISSION: dashing away
    '\U0001f525': 'FIRE:',         # FIRE: fire
    '\U0001f32d': 'WIND:',         # WIND: hot dog (sometimes used for wind)
    
    # Numbers and counting
    '\u0031\ufe0f\u20e3': '1.',    # 1. keycap digit one
    '\u0032\ufe0f\u20e3': '2.',    # 2. keycap digit two
    '\u0033\ufe0f\u20e3': '3.',    # 3. keycap digit three
    '\u0034\ufe0f\u20e3': '4.',    # 4. keycap digit four
    '\u0035\ufe0f\u20e3': '5.',    # 5. keycap digit five
    
    # Additional common Unicode issues
    '\u2192': '->',                # -> rightwards arrow
    '\u2190': '<-',                # <- leftwards arrow
    '\u2194': '<->',               # <-> left right arrow
    '\u2022': '*',                 # * bullet
    '\u25cf': '*',                 # * black circle
    '\u25cb': 'o',                 # o white circle
    '\u25a0': '[X]',               # [X] black square
    '\u25a1': '[ ]',               # [ ] white square
    '\u2660': 'SPADES',            # SPADES black spade suit
    '\u2665': 'HEARTS',            # HEARTS black heart suit
    '\u2666': 'DIAMONDS',          # DIAMONDS black diamond suit
    '\u2663': 'CLUBS',             # CLUBS black club suit
    
    # Time and date
    '\u23f0': 'ALARM:',            # ALARM: alarm clock
    '\u23f1': 'STOPWATCH:',        # STOPWATCH: stopwatch
    '\u23f2': 'TIMER:',            # TIMER: timer clock
    
    # Common scientific symbols
    '\u00b0': 'deg',               # deg degree sign
    '\u00b1': '+/-',               # +/- plus-minus sign
    '\u00b2': '^2',                # ^2 superscript two
    '\u00b3': '^3',                # ^3 superscript three
    '\u03bc': 'micro',             # micro micro sign
    '\u03c0': 'pi',                # pi pi
    '\u2103': 'C',                 # C degree Celsius
    '\u2109': 'F',                 # F degree Fahrenheit
}

# File extensions to check
EXTENSIONS_TO_CHECK = {'.py', '.md', '.txt', '.json', '.csv', '.rst', '.yaml', '.yml'}

# Directories to skip
SKIP_DIRECTORIES = {'.git', '.vscode', '__pycache__', '.pytest_cache', 'node_modules', '.conda'}

class UnicodeFixerResults:
    """Track results of Unicode fixing process"""
    
    def __init__(self):
        self.files_checked = 0
        self.files_modified = 0
        self.unicode_chars_found = {}
        self.errors = []
        self.backup_dir = None

def create_backup_directory():
    """Create a backup directory for original files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"unicode_fix_backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def detect_unicode_issues(text):
    """Detect Unicode characters that might cause encoding issues"""
    issues = []
    
    for char in text:
        # Check for characters outside ASCII range
        if ord(char) > 127:
            char_code = f"\\u{ord(char):04x}" if ord(char) < 65536 else f"\\U{ord(char):08x}"
            issues.append({
                'char': char,
                'code': char_code,
                'replacement': UNICODE_REPLACEMENTS.get(char, f'[U+{ord(char):04X}]')
            })
    
    return issues

def fix_unicode_in_text(text):
    """Replace Unicode characters with ASCII equivalents"""
    fixed_text = text
    replacements_made = []
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_replacements = sorted(UNICODE_REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for unicode_char, replacement in sorted_replacements:
        if unicode_char in fixed_text:
            count = fixed_text.count(unicode_char)
            fixed_text = fixed_text.replace(unicode_char, replacement)
            replacements_made.append({
                'original': unicode_char,
                'replacement': replacement,
                'count': count,
                'code': f"\\u{ord(unicode_char[0]):04x}" if len(unicode_char) == 1 and ord(unicode_char[0]) < 65536 else 'MULTI'
            })
    
    return fixed_text, replacements_made

def should_skip_file(file_path):
    """Check if file should be skipped"""
    # Skip if in excluded directory
    for part in file_path.parts:
        if part in SKIP_DIRECTORIES:
            return True
    
    # Skip if not in allowed extensions
    if file_path.suffix not in EXTENSIONS_TO_CHECK:
        return True
    
    # Skip backup files
    if 'backup' in file_path.name.lower():
        return True
    
    return False

def fix_file_unicode(file_path, backup_dir, results):
    """Fix Unicode issues in a single file"""
    results.files_checked += 1
    
    try:
        # Read file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            original_content = f.read()
        
        # Check for Unicode issues
        issues = detect_unicode_issues(original_content)
        
        if not issues:
            return  # No issues found
        
        # Fix Unicode characters
        fixed_content, replacements = fix_unicode_in_text(original_content)
        
        if not replacements:
            return  # No changes made
        
        # Create backup
        backup_file = backup_dir / file_path.name
        counter = 1
        while backup_file.exists():
            backup_file = backup_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
        
        shutil.copy2(file_path, backup_file)
        
        # Write fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        results.files_modified += 1
        
        # Track changes
        for replacement in replacements:
            char_code = replacement['code']
            if char_code not in results.unicode_chars_found:
                results.unicode_chars_found[char_code] = {
                    'char': replacement['original'],
                    'replacement': replacement['replacement'],
                    'files': [],
                    'total_count': 0
                }
            
            results.unicode_chars_found[char_code]['files'].append(str(file_path))
            results.unicode_chars_found[char_code]['total_count'] += replacement['count']
        
        print(f"   FIXED: {file_path}")
        for replacement in replacements:
            print(f"      {replacement['code']} '{replacement['original']}' -> '{replacement['replacement']}' ({replacement['count']} times)")
    
    except Exception as e:
        error_msg = f"Error processing {file_path}: {e}"
        results.errors.append(error_msg)
        print(f"   ERROR: {error_msg}")

def scan_and_fix_unicode_issues(root_path=None):
    """Scan project and fix Unicode issues"""
    if root_path is None:
        root_path = Path('.')
    else:
        root_path = Path(root_path)
    
    print("UNICODE FIXER FOR GHG EMISSIONS PROJECT")
    print("=" * 50)
    print(f"Scanning directory: {root_path.absolute()}")
    print(f"Target extensions: {', '.join(EXTENSIONS_TO_CHECK)}")
    print(f"Skip directories: {', '.join(SKIP_DIRECTORIES)}")
    print("")
    
    # Create backup directory
    backup_dir = create_backup_directory()
    results = UnicodeFixerResults()
    results.backup_dir = backup_dir
    
    print(f"Backup directory created: {backup_dir}")
    print("")
    
    # Find all files to process
    files_to_process = []
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and not should_skip_file(file_path):
            files_to_process.append(file_path)
    
    print(f"Found {len(files_to_process)} files to check")
    print("")
    
    # Process each file
    for file_path in files_to_process:
        print(f"Checking: {file_path}")
        fix_file_unicode(file_path, backup_dir, results)
    
    # Print summary
    print("\n" + "=" * 50)
    print("UNICODE FIXING COMPLETE")
    print("=" * 50)
    
    print(f"Files checked: {results.files_checked}")
    print(f"Files modified: {results.files_modified}")
    print(f"Backup directory: {results.backup_dir}")
    
    if results.unicode_chars_found:
        print(f"\nUnicode characters fixed:")
        for char_code, info in results.unicode_chars_found.items():
            print(f"  {char_code}: '{info['char']}' -> '{info['replacement']}'")
            print(f"    Found in {len(info['files'])} files, {info['total_count']} total occurrences")
    
    if results.errors:
        print(f"\nErrors encountered:")
        for error in results.errors:
            print(f"  {error}")
    
    if results.files_modified > 0:
        print(f"\nSUCCESS: Fixed {results.files_modified} files!")
        print("Original files backed up to:", results.backup_dir)
        print("\nYou can now run the tests without Unicode encoding errors.")
    else:
        print("\nNo Unicode issues found that needed fixing.")
    
    return results

def test_fixed_files():
    """Test that common files don't have Unicode issues"""
    print("\nTesting fixed files...")
    
    test_files = [
        'tests/test_small_scale.py',
        'tests/test_medium_scale.py', 
        'tests/test_large_scale.py',
        'src/preprocessing/data_loader.py',
        'run_analysis.py'
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to encode with cp1251 (Windows default)
                content.encode('cp1251')
                print(f"  OK: {test_file}")
                
            except UnicodeEncodeError as e:
                print(f"  STILL HAS ISSUES: {test_file} - {e}")
            except Exception as e:
                print(f"  ERROR: {test_file} - {e}")
        else:
            print(f"  NOT FOUND: {test_file}")

if __name__ == "__main__":
    import sys
    
    # Get root directory from command line or use current directory
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    try:
        results = scan_and_fix_unicode_issues(root_dir)
        test_fixed_files()
        
        print(f"\nTo test the fixes, try running:")
        print("python run_analysis.py --test small")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
