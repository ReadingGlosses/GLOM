import os
import sys
import argparse
from fpdf import FPDF
from ursus.rules import Rule
from ursus.segbase import Segbase

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

def read_dictionary_files(cwd, dictionary_dir ):
    lexicon = dict()
    path = os.path.join(cwd, dictionary_dir)
    for file in os.listdir(path):
        with open(os.path.join(path, file), encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        sep = ',' if len(lines[0].split(',')) > 1 else '\t'
        for line in lines:
            if not line:
                continue
            gloss,translation = line.strip().replace('-','').split(sep)[:2] #ignore any other data for now
            # if translation_first:
            #     gloss,translation = translation,gloss
            lexicon[gloss.replace('-','')] = translation
    return lexicon

def read_paradigm_files(cwd, paradigm_dir):
    paradigms = dict()
    paradigm_dir = os.path.join(cwd, paradigm_dir)
    for file in os.listdir(os.path.join(cwd, paradigm_dir)):
        with open(os.path.join(cwd, paradigm_dir, file), encoding='utf-8') as f:
            lines = [line for line in f]
            sep = ',' if len(lines[0].split(','))>1 else '\t'
        if lines[0].startswith(sep):
            columns = lines[0].strip().split(sep)[1:]  # first column 'header' is always empty
        else:
            columns = ['']
        #rows = [line.strip().split(sep) for line in lines[1:]]
        rows = list()
        for line in lines[1:]:
            if '#' in line:
                line, comment = line.split('#')
            row = line.strip().split(sep)
            rows.append(row)
        gloss = file.split('.')[0]
        paradigms[gloss] = dict()
        for row in rows:
            paradigms[gloss][row[0]] = dict()
            for j, col in enumerate(columns):
                morpheme = row[j + 1]  # offset because first column is empty
                if not col:
                    paradigms[gloss][row[0]] = morpheme
                else:
                    paradigms[gloss][row[0]][col] = morpheme
    return paradigms

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
                    if '.' in morpheme:
                        morphs = morpheme.split('.')
                        paradigm = morphs[0]
                        row = morphs[1]
                        try:
                            col = morphs[2]
                        except IndexError:
                            col = None
                        if col is not None:
                            new_word.append(paradigms[paradigm][row][col])
                        else:
                            new_word.append(paradigms[paradigm][row])
                    else:
                        lexicon, result, errors = query_lexicon(lexicon, morpheme, errors)
                        new_word.append(result)
                else:
                    lexicon, result, errors = query_lexicon(lexicon, morpheme, errors)
                    new_word.append(result)

            new_word = '-'.join(new_word)
            new_sentence.append(new_word)
        new_sentence = ' '.join(new_sentence)
        output.append(new_sentence)
    return output, errors

def read_input_file(cwd, input_file, translation_first):
    with open(os.path.join(cwd, input_file), encoding='utf-8') as f:
        lines = [line.strip() for line in f]
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
            if translation_first:
                 gloss,translation = translation,gloss
        glosses.append(gloss)
        translations.append(translation)
    return glosses, translations

def generate_output_file(file_format, output_file, top_lines, morpheme_breakdowns, glosses, translations, add_sentence_numbers):

    example = str()
    sentence_number = 0
    if file_format == 'text':
        with open(output_file, mode='w', encoding='utf-8') as f:
            for j in range(len(glosses)):
                if add_sentence_numbers:
                    sentence_number += 1
                example = align_glosses(top_lines[j], morpheme_breakdowns[j], glosses[j], translations[j], sentence_number)
                print(example, file=f)
    elif file_format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for j in range(len(glosses)):
            if add_sentence_numbers:
                sentence_number += 1
            example = align_glosses(morpheme_breakdowns[j], glosses[j], translations[j], sentence_number)
            pdf.cell(200, 10, txt=example, ln=True)
        pdf.output(output_file)

    return example

def apply_sound_changes(examples, cwd, sound_change_file):
    if not sound_change_file:
        return [e.replace('-', '') for e in examples]

    segbase = Segbase()

    with open(os.path.join(cwd, sound_change_file)) as f:
        rules = [Rule(line.strip()) for line in f if line.strip()]

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
                      translation_first=False,
                      sound_change_file=None,
                      print_one=False):
    cwd = os.getcwd()
    lexicon = read_dictionary_files(cwd, dictionary_dir)
    paradigms = read_paradigm_files(cwd, paradigm_dir)
    glosses, morphemes = read_input_file(cwd, input_file, translation_first)
    morpheme_breakdowns, errors = get_morphemes(glosses, lexicon, paradigms)
    top_lines = apply_sound_changes(morpheme_breakdowns, cwd, sound_change_file)
    example_sentence = generate_output_file(file_format, output_file, top_lines, morpheme_breakdowns, glosses, morphemes, add_sentence_numbers)

    if errors:
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



if __name__ == '__main__':
    if sys.argv[0]:
        parser = argparse.ArgumentParser(prog='GLOM', description='A tool for building glossed linguistic examples')
        parser.add_argument('-i', '--input_file', dest='input_file', default='sentences.txt', help='(Required) Name of file with sentences for processing', required=True)
        parser.add_argument('-o', '--output_file', dest='output_file', default='new_sentences.txt', help='(Required) Name of file for writing output (glossed sentences)', required=True)
        parser.add_argument('-d', '--dictionary_dir', dest='dictionary_dir', default='dictionaries', help='(Optional) Name of local directory containing dictionary files.', required=False)
        parser.add_argument('-p', '--paradigm_dir', dest='paradigm_dir', default='paradigms', help='(Optional) Name of local directory containing paradigm files', required=False)
        parser.add_argument('-f', '--file_format', dest='file_format', default='text', required=False, help='(Optional) Choose format for the output file, options are text or pdf, defaults to text')
        parser.add_argument('-n', '--numbered_examples', dest='add_sentence_numbers', default=False, action='store_true', required=False, help='(Optional) Use this flag to add a number to each output sentence')
        parser.add_argument('-tf', '--translation_first', dest='translation_first', default=False, action='store_true', required=False, help='(Optional) Indicates that dictionary files are formatted as translation then gloss')
        parser.add_argument('-sc', '--sound_changes', dest='sound_change_file', default=False, required=False, help='(Optional) Name of local file containing sound change rules. See GLOM documentation for more details.')
        parser.add_argument('-p1', '--print_one', dest='print_one', default=False, action='store_true', required=False, help='(Optional) include this flag if you want to see one example sentence printec in the console when GLOM is done.')
        args = parser.parse_args()
        construct_examples(**vars(args))

