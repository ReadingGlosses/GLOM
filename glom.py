import os
import sys
import re
import argparse
import sys
from fpdf import FPDF
from ursus.rules import Rule
from ursus.segbase import Segbase

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def query_lexicon(lexicon, morpheme, errors):
    try:
        result = lexicon[morpheme]
    except KeyError:
        lexicon[morpheme] = '?'
        result = '?'
        errors.append(morpheme)
    return lexicon, result, errors

def align_glosses(top_line, morpheme_breakdown, glosses, translation, number=0):
    top_line = top_line
    morphemes = morpheme_breakdown.split()
    glosses = glosses.split()
    translation = translation

    max_lengths = [max(len(word1), len(word2)) for word1, word2 in zip(morphemes, glosses)]

    aligned_morphemes = [word1 + ' ' * (max_length - len(word1) + 1) for word1, max_length in zip(morphemes, max_lengths)]
    aligned_glosses = [word2 + ' ' * (max_length - len(word2) + 1) for word2, max_length in zip(glosses, max_lengths)]

    morphemes = ''.join(aligned_morphemes)
    gloss = ''.join(aligned_glosses)

    #plain_text = ' '.join([''.join(morph.split('-')) for morph in top_line]).replace('@','')

    if number:
        prefix = f'{number}. '
        buffer = ' '*len(prefix)
        top_line = prefix + top_line
        morphemes = buffer + morphemes
        gloss = buffer + gloss
        translation = buffer + translation

    return '\n'.join([top_line, morphemes, gloss, translation, '\n']) #return extra newline for nice formatting

def read_dictionary_files(cwd, dictionary_dir, dictionary_order):
    lexicon = dict()
    path = os.path.join(cwd, dictionary_dir)
    #path = resource_path(dictionary_dir)
    for file in os.listdir(path):
        try:
            with open(os.path.join(path, file), encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
        except KeyError:
            print(f'GLOM tried to open the dictionary file "\\dictionaries\\f{os.path.join(path,file)}" but could not find it. Check the spelling and make sure you have a folder called "{dictionary_dir}"')
            sys.exit()
        sep = ',' if len(lines[0].split(',')) > 1 else '\t'
        for line in lines:
            if not line:
                continue
            gloss,morpheme = line.strip().replace('-','').split(sep)[:2] #ignore any other data for now
            if dictionary_order.startswith('morph'):
                 gloss,morpheme = morpheme,gloss
            lexicon[gloss] = morpheme
    return lexicon

def read_paradigm_files(cwd, paradigm_dir, table_order):
    paradigms = dict()
    paradigm_dir = os.path.join(cwd, paradigm_dir)
    #paradigm_dir = resource_path(paradigm_dir)
    for file in os.listdir(os.path.join(cwd, paradigm_dir)):
        try:
            #with open(os.path.join(cwd, paradigm_dir, file), encoding='utf-8') as f:
            with open(os.path.join(paradigm_dir, file), encoding='utf-8') as f:
                data = f.read()
        except KeyError:
            print(f'GLOM tried to open a paradigm file called "{file}" but could not find it. Make sure the spelling is correct and that the folder {paradigm_dir} exists.')
            sys.exit()
        if '#' in data:
            data,comments = data.strip().split('#')
        sep = ',' if len(data[0].split(',')) > 1 else '\t'
        blocks = re.split(r'\n\s*\n', data.strip())
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            rows = [b.split(',') for b in block.split('\n')]
            second_row = rows[1]

            if len([x for x in second_row if x.isupper()])>2:
                #if there are at least two upper-case glosses in the second row, it's not a 2-dimenational table
                for line in block.strip().split("\n"):
                    parts = line.split(",")
                    *keys, value = parts
                    current_level = paradigms

                    for key in keys[:-1]: #ignore final value, it's the transcription
                        if key not in current_level:
                            current_level[key] = {}
                        current_level = current_level[key]

                    # Set the final value
                    current_level[keys[-1]] = value

            else:
                #read this as a classic 2D table where the top left element is the starting point of the gloss
                headers, rows = rows[0], rows[1:]
                gloss, columns = headers[0], headers[1:]
                if table_order.startswith('col'):
                    rows,columns = columns,rows
                paradigms[gloss] = dict()
                for row in rows:
                    row_header, row_data = row[0], row[1:]
                    paradigms[gloss][row_header] = dict()
                    for j, col in enumerate(columns):
                        morpheme = row_data[j]
                        paradigms[gloss][row_header][col] = morpheme

    return paradigms

def paradigm_lookup(sequence, dictionary):
    keys = sequence.split(".")
    result = dictionary
    for key in keys:
        result = result[key]
    return result

def get_morphemes(glosses, lexicon, paradigms):
    output = list()
    errors = list()
    for g in glosses:
        new_sentence = list()
        for word in g.split():
            new_word = list()
            for morpheme in word.strip().split('-'):
                if morpheme.islower():
                    lexicon, result, errors = query_lexicon(lexicon, morpheme, errors)
                    new_word.append(result)
                elif morpheme.isupper():
                    try:
                        if '.' in morpheme:
                            morph = paradigm_lookup(morpheme, paradigms)
                            new_word.append(morph)
                            # morphs = morpheme.split('.')
                            # paradigm = morphs[0]
                            # row = morphs[1]
                            # try:
                            #     col = morphs[2]
                            # except IndexError:
                            #     col = None
                            # if col is not None:
                            #     new_word.append(paradigms[paradigm][row][col])
                            # else:
                            #     new_word.append(paradigms[paradigm][row])
                        else:
                            lexicon, result, errors = query_lexicon(lexicon, morpheme, errors)
                            new_word.append(result)
                    except KeyError as e:
                        if not e:
                            continue
                        print(f'Something went wrong trying to read your input file.')
                        print(f'While reading this gloss:{word}')
                        print(f'GLOM encountered an error on this particular item:{e}')
                        print('One of the following things probably happened:')
                        print('- Simple spelling mistake. Maybe you typed INFL instead of INF, or 1POSS instead of 1.POSS')
                        print('- Inconsistent glossing. Maybe you used "SG" for singular in one place and "SING" in another')
                        print('- One of your paradigm files might have an extra comma or tab at the end of a line. Delete these.')
                        print('- You might have reversed the order of information in a table. GLOM reads rows before columns by default, run with "--table_order column" if you prefer the columns first.')
                        print('- You might have forgotten an element in your gloss. If your nominative case inflects for number and gender, make sure they are both included.')
                        quit()
                else:
                    lexicon, result, errors = query_lexicon(lexicon, morpheme, errors)
                    new_word.append(result)
            new_word = '-'.join(new_word)
            new_sentence.append(new_word)
        new_sentence = ' '.join(new_sentence)
        output.append(new_sentence)
    return output, errors

def read_input_file(cwd, input_file, input_order):
    try:
        with open(os.path.join(cwd, input_file), encoding='utf-8') as f:
        #with open(resource_path(input_file), encoding='utf-8') as f:
            lines = [line.strip() for line in f]
    except FileNotFoundError:
        print(f'GLOM tried opening the intput file "{input_file}" but could not find it. Make sure the name is typed correctly, and that it is in the same folder as GLOM.')
        sys.exit()

    glosses = list()
    translations = list()
    sep = ',' if len(lines[0].split(',')) > 1 else '\t'

    for line in lines:
        if not line:
            continue
        line = line.split(sep)

        if len(line) == 1:
            gloss = line[0]
            translation = ''
        else:
            gloss,translation = line
            if input_order == 'translation':
                 gloss,translation = translation,gloss
        glosses.append(gloss)
        translations.append(translation)
    return glosses, translations

def generate_output_file(file_format, output_file, top_lines, morpheme_breakdowns, glosses, translations, add_sentence_numbers):

    example = str()
    sentence_number = 0
    if file_format in ['txt', 'text']:
        if not output_file.endswith('.txt'):
            output_file = output_file.split('.')[0] + '.txt'
        with open(output_file, mode='w', encoding='utf-8') as f:
            for j in range(len(glosses)):
                if add_sentence_numbers:
                    sentence_number += 1
                example = align_glosses(top_lines[j], morpheme_breakdowns[j], glosses[j], translations[j], sentence_number)
                print(example, file=f)
    elif file_format == 'pdf':
        if not output_file.endswith('.pdf'):
            output_file = output_file.split('.')[0]  + '.pdf'
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=12)
        line_height = 5
        pdf.set_font("Arial", size=12)
        for j in range(len(glosses)):
            if pdf.get_y() + (line_height * 4) > pdf.page_break_trigger:
                pdf.add_page()

            if add_sentence_numbers:
                sentence_number += 1
            example = align_glosses(top_lines[j], morpheme_breakdowns[j], glosses[j], translations[j], sentence_number)
            pdf.multi_cell(0, line_height, txt=example)
        pdf.output(output_file)

    return example

def apply_sound_changes(examples, cwd, sound_change_file):
    if not sound_change_file:
        return [e.replace('-', '') for e in examples]

    segbase = Segbase(path=resource_path(os.path.join('ursus','data','ipa2spe.txt')))

    try:
        path = os.path.join(cwd, sound_change_file)
        #path = resource_path(sound_change_file)
        with open(path, encoding='utf-8') as f:
            rules = [Rule(line.strip()) for line in f if line.strip()]
    except FileNotFoundError as e:
        print(f'You specified a sound change file called "{sound_change_file}" but GLOM could not find it. Double check the name and spelling. The file must be in the same folder as the GLOM program.')
        sys.exit()

    output = list()
    for e in examples:
        words = e.split()
        results = list()
        for word in words:
            if word == '?':
                results.append('?')
                continue
            word = word.replace('-','')
            for rule in rules:
                word, applied = rule.apply(word, segbase)
            results.append(word)
        output.append(' '.join(results))
    return output

def construct_examples(input_file,
                      output_file,
                      dictionary_dir='dictionaries',
                      paradigm_dir='paradigms',
                      add_sentence_numbers=False,
                      file_format='text',
                      input_order ='translation',
                      dictionary_order = 'gloss',
                      sound_change_file=None,
                      print_one=False,
                      table_order='rows'):
    cwd = os.getcwd()
    lexicon = read_dictionary_files(cwd, dictionary_dir, dictionary_order)
    paradigms = read_paradigm_files(cwd, paradigm_dir, table_order)
    glosses, morphemes = read_input_file(cwd, input_file, input_order)
    morpheme_breakdowns, errors = get_morphemes(glosses, lexicon, paradigms)
    top_lines = apply_sound_changes(morpheme_breakdowns, cwd, sound_change_file)
    example_sentence = generate_output_file(file_format, output_file, top_lines, morpheme_breakdowns, glosses, morphemes, add_sentence_numbers)

    if len(errors)>0:
        print(f'WARNING: The following {len(errors)} items in your input file could not be located in any dictionary or paradigm:\n')
        print(','.join(sorted([str(e) for e in errors])))
        print(f'\nThese have been replaced by \'?\' in {output_file}.')

    message = f'Done! Check the file "{output_file}" for your glossed examples'
    print('#'*(len(message)+5))
    print('# ', message, '#')
    print('#'*(len(message)+5))

    if print_one:
        print()
        print('Here is the last sentence from your input file:\n ')
        print(example_sentence)

    return errors


if __name__ == '__main__':
    if sys.argv[0]:
        parser = argparse.ArgumentParser(prog='GLOM', description='A tool for building glossed linguistic examples')
        parser.add_argument('-i', '--input_file', dest='input_file', default='sentences.txt', help='(Required) Name of file with sentences for processing', required=True)
        parser.add_argument('-o', '--output_file', dest='output_file', default='new_sentences.txt', help='(Required) Name of file for writing output (glossed sentences)', required=True)
        parser.add_argument('-d', '--dictionary_dir', dest='dictionary_dir', default='dictionaries', help='(Optional) Name of local directory containing dictionary files.', required=False)
        parser.add_argument('-p', '--paradigm_dir', dest='paradigm_dir', default='paradigms', help='(Optional) Name of local directory containing paradigm files', required=False)
        parser.add_argument('-f', '--file_format', dest='file_format', default='text', required=False, help='(Optional) Choose format for the output file, options are text or pdf, defaults to text')
        parser.add_argument('-n', '--numbered_examples', dest='add_sentence_numbers', default=False, action='store_true', required=False, help='(Optional) Use this flag to add a number to each output sentence')
        parser.add_argument('-io', '--input_order', dest='input_order', default='translation', required=False, help='(Optional) Input files are ordered translation-first by default. Set this argument to "gloss" if you want the revered order')
        parser.add_argument('-do', '--dictionary-order', dest='dictionary_order', default='gloss', required=False, help='(Optional) Dictionary files are ordered gloss-first by default. Set this argument to "morpheme" if you want the reversed order')
        parser.add_argument('-sc', '--sound_changes', dest='sound_change_file', default=False, required=False, help='(Optional) Name of local file containing sound change rules. See GLOM documentation for more details.')
        parser.add_argument('-p1', '--print_one', dest='print_one', default=False, action='store_true', required=False, help='(Optional) include this flag if you want to see one example sentence printed in the console when GLOM is done.')
        parser.add_argument('-to', '--table_order', dest='table_order', default='row', required=False, help='(Optional) Paradigm tables are read in the order of rows then columns. Set this argument to "columns" if you want the reversed order')
        args = parser.parse_args()
        construct_examples(**vars(args))

