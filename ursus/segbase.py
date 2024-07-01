#!/usr/bin/env python
#-*- coding: utf-8 -*-

import codecs
import random
import itertools
import os
from .phonology import *
import string

class Segbase(object):
    """
    This object contains all of the Segments that could potentially appear in a PyILM simulation
    It is only created once per simulation and remains constant throughout a simulation.
    path : the path to a feature file, probably ipa2spe.txt
    restricted_features: if None, use all feature, if 'some' then omit features that tend to have 'n' or '0' labelling
    such as covered or del_release
    delimiter: delimiter character for the feature file
    give_details: similar to a 'verbose' flag, but might not work
    n_value = if a feature in the feature file has an 'n' value (instead of + or -), this specified what to replace it with
              it can be replace by another 'n' if you don't need binary features
    dot_value = same as 'n' value, but for features that have a . instead
    init_seg_groups = if True, the segments in Segbase are divided into groups based on approximate complexity (not working)
    phoneme_prediction = what to do when trying to generate a label from a set of features. 'rules' uses some basic
    rules to compare +/- values and pick symbol with most matches, 'model' loads a feedforward network trained to predict
    phoneme symbols based on phonological features
    """

    def __init__(self,path=None, restricted_features=None, delimiter=',', givedetails=False,
                 n_value=None, dot_value=None, init_seg_groups=False, phoneme_prediction='rules'):

        if path is None:
            path = os.path.join(os.getcwd(), 'ursus', 'data', 'ipa2spe.txt')

        if restricted_features is None:
            restricted_features = list()
        elif restricted_features == 'some':
            restricted_features = ['voc','son','cont','voice','nasal','cor','ant',
                'round', 'back','low','high','distr','tense','strid','lat','glotcl',
                'delrel','hisubglpr','mvglotcl']
        #otherwise restricted_features is a user-supplied list of features

        self.segments = dict()
        self.givedetails = givedetails
        self.seg_count = -1

        with codecs.open(path,mode='r', encoding='utf-8') as file_:
            for line in file_.readlines():
                if line == '\n':
                    continue
                line = line.lstrip(u'\ufeff')
                line = line.strip()
                line = line.split(delimiter)
                name = line[0]
                features = line[1:]

                if not restricted_features:
                    self.segments[name] = Segment(name, features, None)

                else:
                    feature_list = [f for f in features if f[1:] in restricted_features]
                    self.segments[name] = Segment(name, feature_list, None)

        if restricted_features:
            self.features = restricted_features
        else:
            self.features = [f[1:] for f in features] #pick up from last loop

        for seg in self.segments.values():
            for feature in seg.features:
                if seg.features[feature].sign=='n':
                    if n_value is None:
                        n_value = random.choice(['+', '-'])
                    else:
                        n_value = 'n'
                    seg.features[feature].sign = n_value

        for seg in self.segments.values():
            for feature in seg.features:
                if seg.features[feature].sign=='.':
                    if dot_value is None:
                        dot_value = random.choice(['+', '-'])
                    else:
                        dot_value = '.'
                    seg.features[feature].sign = dot_value

        self.consonants = [seg for seg in self.segments if self.segments[seg].features['voc'] == '-voc']
        self.vowels = [seg for seg in self.segments if self.segments[seg].features['voc'] == '-voc']
        self.created_seg_groups = False
        if init_seg_groups:
            self.init_seg_groups()
        self.phoneme_prediction = phoneme_prediction
        if self.phoneme_prediction == 'model':
            self.phoneme_labeller = PhonemeLabeller('best_model_restricted_features.h5',
                                                [segment for segment in self.segments])



    def get_consonants(self):
        return self.consonants

    def get_vowels(self):
        return self.vowels

    def get_segs(self, group):
        if group==1 or group=='simple':
            return self.set1
        elif group==2 or group=='elaborated':
            return self.set2
        elif group==3 or group=='complex':
            return self.set3
        else:
            raise ValueError('Not a valid group. Use 1,2,3 or simple,elaborated,complex')


    def __iter__(self):
        for seg in self.segments:
            yield seg

    def __contains__(self,seg):
        return seg in self.segments

    def __getitem__(self,seg):
        return self.segments[seg]

    def random_inventory(self, size, restriction=None, return_strings=False):
        """
        size            tuple, (C,V) = number of consonants and vowels
        restriction     the string 'simple' or a list of features or None
        return_strings  bool, if True return a list of str, else a list of Segments
        """

        C = [s for s in self.segments.values() if not '+voc' in s.features.values()] if size[0] > 0 else []
        V = [s for s in self.segments.values() if '+voc' in s.features.values()] if size[1] > 0 else []
        selection = list()

        if restriction is None:
            c = random.sample(C, size[0])
            v = random.sample(V, size[1])
            selection.extend(c)
            selection.extend(v)

        elif restriction == 'simple':
            if not self.created_seg_groups:
                self.init_seg_groups()
            #return Lindblom & Maddieons type "simple segments"
            c = random.sample(self.get_segs(1), size[0])
            #v = random.sample(self.get_segs(1), size[1])
            v = random.sample(V, size[1])
            selection.extend(c)
            selection.extend(v)

        else:
            c = list()
            v = list()
            while len(c)<= size[0]:
                seg = random.choice(C)
                if all(seg.features[feature[1:]]==feature for feature in restriction):
                    c.append(seg)
            while len(v)<= size[1]:
                seg = random.choice(V)
                if all(seg.features[feature[1:]]==feature for feature in restriction):
                    v.append(seg)
            selection.extend(c)
            selection.extend(v)

        if return_strings:
            selection = [s.symbol for s in selection]

        return selection

    def random_seg(self, exclude=None):
        if exclude is None:
            exclude = list()
        segs = [s for s in self.segments.keys() if not s in exclude]
        return random.choice(segs)

    def seg_as_int(self):
        self.seg_count += 1
        return str(self.seg_count)

    def copy_seg(self,symbol):
        """
        Return a new Segment object, not a reference to a segbase object
        """
        features = self.segments[symbol].features.copy()
        symbol = self.segments[symbol].symbol[:]
        return Segment(symbol,features,None)

    def choose_symbol_from_tokens(self, sound, exclude=None):
        """
        Only returns a symbol, a unicode string, that matches some features
        This does NOT return a segment
        To get a segment, call segbase.choose_segment_from_tokens
        """

        if exclude is None:
            exclude = tuple()

        feature_list = list()
        for token in sound.features.values():
            if token.value > .50:
                sign = '+'
            elif token.value <= 0:
                sign = 'n'
            elif token.value <= .5:
                sign = '-'
            elif token.value == '.':
                sign = '.'

            feature_list.append(sign+token.name)

        return self.choose_symbol_from_features(feature_list,exclude)

    def choose_segment_from_tokens(self,sound,exclude=()):
        """
        Only returns a Segment object, with an empty .envs,
        Calls segbase.choose_symbol_from_tokens to get a symbol
        """

        symbol = self.choose_symbol_from_tokens(sound,exclude)
        features = self.segments[symbol].features.copy()
        return Segment(symbol,features,None)

    def find_minimum_contrasts(self,inventory):

        inventory = [self.segments[seg] for seg in inventory]
        contrasts = list()
        for seg1,seg2 in itertools.product(inventory,inventory):
            if seg1.symbol == seg2.symbol:
                continue
            for f1,f2 in zip(seg1.features.values(), seg2.features.values()):
                if f1 != f2:
                    contrasts.append(f1.name)
            contrasts = list(set(contrasts)) #remove any duplicates
            if len(contrasts) >= len(self.features):
                break #everything is contrastive


        return contrasts

    def convert_features_to_binary(self, input_features, non_binary=0):
        """
        take a list of features and return a binary number
        [+voice, -cont, +back] -> 101
        the non_binary argument signals what value to use if the input feature has
        a value like 'n' or '0', if set to None, then any segment with a non-binary
        feature is removed from the set
        """
        binary_features = list()
        for feature in input_features:
            if feature.sign == '+':
                binary_features.append(1)
            elif feature.sign == '-':
                binary_features.append(0)
            else:
                if non_binary is None:
                    #raise TypeError('Input feature contains non-binary feature')
                    return False
                else:
                    binary_features.append(non_binary)
        return binary_features


    def choose_symbol_from_features(self, input_list, exclude=None):
        """
        Takes a list of Feature objects as input, and finds an IPA symbol
        that would best represent that collection of features. This function
        returns only that symbol (i.e. a string), not a Segment object.
        The exclude argument is a list of strings of symbols already
        in use and should not be considered. Typically, you would pass an agent's
        inventory as the exclude value.
        """
        if exclude is None:
            exclude = tuple()

        input_list.sort(key=lambda x: x[1])  # sort by feature name
        input_list = [f[0] for f in input_list]  # just get values, ignore names

        if self.phoneme_prediction == 'model':
            #load a trained feedforward network that will predict a symbol
            #the model was trained to predict an IPA symbol (one-hot encoded) based on a binary feature input
            selected_seg = self.phoneme_labeller.predict_label(input_list)

        elif self.phoneme_prediction == 'rules':
            #use a set of rules to find the 'best' match
            #it compares the features values of the input set against all segbase segments and takes the highest score
            #in case of a tie, randomly select from the highest-scoring matches

            seg_scores = dict()
            segs = ((key,value.features) for (key,value) in self.segments.items() if key not in exclude)

            for symbol,features in segs:
                score = 0
                features = [str(features[f]) for f in features]
                features.sort(key=lambda x:x[1])
                features = [f[0] for f in features] #just get the values
                score = sum([1 if f1==f2 else 0 for f1,f2 in zip(input_list, features)])
                seg_scores[symbol] = score
                if score == len(input_list): #max score
                    return self.segments[symbol]

            max_ = max(seg_scores.values())
            top_scores = [seg for seg in seg_scores.keys() if seg_scores[seg] == max_]
            selected_seg = random.choice(top_scores)



        return self.segments[selected_seg]

class Pbase(object):
    """
    This opens the inventories of P-base as a Python object
    P-base is a database of phonological inventories created by Dr. Jeff Mielke
    An online version of P-base is available at http://pbase.phon.chass.ncsu.edu/
    A downloadable version is available at http://aix1.uottawa.ca/~jmielke/pbase/

    To make use of this class you will need to download P-base. The path to the main P-base folder has to
    be provided to the __init__

    """
    def __init__(self, pbase_path):
        alphabet = [letter for letter in string.ascii_uppercase]
        alphabet.append('!')
        self.languages = dict()
        for letter in alphabet:
            filename = ''.join(['pdata_',letter,'.txt'])
            with open(os.path.join(pbase_path, filename), encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
            found_inventory = False
            for line in lines:
                line = line.strip()
                if line.startswith('%'):
                    continue #this symbol acts as a comment symbol in pdata files
                if found_inventory:
                    inventory = [seg for seg in line.split(',') if seg]
                    if 'ISOLATE' in family:
                        family = 'Isolate'
                    self.languages[name] = Language(name, family, location, inventory, langcode)
                    found_inventory = False
                elif line.startswith('Language'):
                    name = line.split(',', 1)[-1]
                elif line.startswith('Family'):
                    family = line.split(',')[-1]
                elif line.startswith('Location'):
                    location = line.split(',')[-1]
                elif line.startswith('Langcode'):
                    langcode = line.split(',')[-1]
                elif line.split(',')[-1] == 'Core':  # core inventory
                    found_inventory = True


        sb = Segbase()
        for language in self.languages.values():
            language.partition_inventory(sb)

    def __iter__(self):
        for language in self.languages.values():
            yield language

    def __len__(self):
        return len(self.languages)

    def __getitem__(self, item):
        return self.languages[item]


class Language(object):

    def __init__(self, name, family, location, inventory, code):
        self.name = name.replace(',','')
        self.family = family[0].upper()+family[1:].lower()
        self.family = self.family.replace(',','')
        self.location = location.replace(',','')
        self.inventory = inventory
        self.consonants = list()
        self.vowels = list()
        self.code = code
        if self.family == 'Isolate':
            self.is_isolate = True
        else:
            self.is_isolate = False
        if '(' in self.family:
            name = self.family.strip(')')
            name = self.family.split('(')
            self.super_family = name[0].strip()
        else:
            self.super_family = self.family

    def partition_inventory(self, segbase):
        for seg in self.inventory:
            if seg in segbase.consonants:
                self.consonants.append(seg)
            else:
                self.vowels.append(seg)



if __name__ == '__main__':

    segbase = Segbase()
    # labeler = PhonemeLabeller('best_model.h5', segbase)
    input = [Feature(random.choice(['+', '-']), str(j)) for j in range(25)]
    print(input)
    prediction = segbase.phoneme_labeller.predict_label(input)
    print(prediction)


