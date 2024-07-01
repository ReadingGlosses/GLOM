class Rule:

    def __init__(self, text):
        lhs, rhs = text.split('/')
        a, b = lhs.split('->')
        self.a = a.strip().strip('{}[]').split(',')
        self.b = b.strip() #this is the output symbol, it can't have any variations

        if rhs.strip().endswith('_'):
            rhs = rhs+'*'
        if rhs.strip().startswith('_'):
            rhs = '*'+rhs

        c, d = rhs.split('_')
        self.c = c.strip().strip('{}[]').split(',')
        self.d = d.strip().strip('{}[]').split(',')

    def matches(self, word_segment, rule_segment, pbase):
        if word_segment == '?':
            return False

        if rule_segment[0] == '*':
            return True

        if word_segment == '#':
            if rule_segment == ['#']:
                return True
            else:
                return False

        if rule_segment[0][0] in ['+', '-']:
            #we are checking against a feature bundle
            #rule_segment will be a list like ['+nasal', '-vocalic']
            #if all the features in rule segment are also in word segment, return True
            word_segment = pbase.segments[word_segment]
            if all([feature in word_segment.feature_list for feature in rule_segment]):
                return True

        else:
            #we are checking against a segment
            #rule segment will be a list like ['p'] in this case
            if word_segment in rule_segment:
                return True

        return False

    def transform(self, segment, pbase):
        if self.b[0] in ['+', '-']:
            b_features = self.b.split(',')
            #it's a feature bundle, we have to transform the input segment's feature list and look up a new symbol
            seg_features = ','.join(pbase.segments[segment].feature_list)
            for b_feature in b_features:
                b_sign = b_feature[0]
                b_name = b_feature[1:]
                if b_sign == '+':
                     seg_features = seg_features.replace('-'+b_name, b_feature)
                elif b_sign == '-':
                    seg_features = seg_features.replace('+'+b_name, b_feature)
            seg_features = seg_features.split(',')
            new_segment = pbase.choose_symbol_from_features(seg_features)
            return new_segment.symbol

        else:
            #it's just a single segment, basic replacement
            return self.b

    def apply(self, word, pbase):
        applied = False
        new_word = [w for w in word] #this crucially assumes there are no digraphs!
        for index, segment in enumerate(word[:]):
            #print(self.a)
            if self.a == ['@'] or self.a == ['Ø']:
                #it's an insertion rule
                check_left = word[index-1] if index > 0 else '#'
                check_right = segment
                #print('environment:', check_left, check_right)
                if self.matches(check_left, self.c, pbase) and self.matches(check_right, self.d, pbase):
                    applied = True
                    new_word.insert(index, self.b)
                    #print('applied!')
                    #print(new_word)
            if self.matches(segment, self.a, pbase):
                check_left = new_word[index-1] if index > 0 else '#'
                check_right = new_word[index+1] if index < len(word)-1 else '#'
                if self.matches(check_left, self.c, pbase) and self.matches(check_right, self.d, pbase):
                    applied = True
                    #new_word.append(self.transform(segment))
                    new_word[index] = self.transform(segment, pbase)
                else:
                    pass #no rules apply

            else:
                pass #current segment isn't a trigger for this rule

        new_word = ''.join(new_word)
        new_word = new_word.replace('@', '') #these are placeholders where deletion occured
        new_word = new_word.replace('Ø', '') #these are placeholders where deletion occured
        return new_word, applied

    def process_segment(self, seg):
        seg = seg.strip().strip('{}').split(',')
        return seg

    def __str__(self):
        a = ''.join(self.a)
        b = self.b
        c = ''.join(self.c)
        d = ''.join(self.d)
        return f'{a} -> {b} / {c} _ {d}'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return str(self) == str(other)

