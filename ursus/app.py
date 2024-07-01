from flask import Flask, render_template, request, jsonify, Response, session
import csv
import os
from io import StringIO
import segbase
from rules import Rule
pbase = segbase.Segbase('data/ipa2spe.txt')

app = Flask(__name__)
app.secret_key = 'FLASK_SECRET'

# rules = list()
# words = list()
# word_entries = [{"word": "", "result": ""}]

@app.route('/')
def index():
    #if not 'rules' in session:
    session['rules'] = list()
    return render_template('index.html', rules=session['rules'])#, word_entries=word_entries)

# @app.route('/add_rule', methods=['POST'])
# def add_rule():
#     rule = request.form['rule']
#     rules.append(Rule(rule))
#     return jsonify(success=True)

@app.route('/add_rule', methods=['POST'])
def add_rule():
    rule = request.form['rule']
    if 'rules' not in session:
        session['rules'] = [rule]
    else:
        ruleset = session['rules']
        ruleset.append(rule)
        session['rules'] = ruleset
    return jsonify(success=True)

@app.route('/apply_rules', methods=['POST'])
def apply_rules():
    data = request.get_json()
    words = data['words']
    results = list()
    rules_applied = list()
    rules_to_ignore = data['ignoreRules']
    print(rules_to_ignore)
    for word in words:
        rules_for_this_word = list()
        for rule in session['rules']:
            if str(rule) in rules_to_ignore:
                applied = False
            else:
                word, applied = Rule(rule).apply(word, pbase)
            if applied:
                rules_for_this_word.append(str(rule))
        results.append(word)
        rules_applied.append('<br>'.join(rules_for_this_word))

    changes = [{"word": word, "result": result, "rules_applied": applied} for (word, result, applied) in zip(words, results, rules_applied)]
    session['rules_table'] = changes
    return jsonify(word_entries=changes)

@app.route('/remove_rule', methods=['POST'])
def remove_rule():
    index = request.form['index']
    index = int(index)
    if 'rules' in session:
        ruleset = session['rules']
        ruleset.pop(index)
        session['rules'] = ruleset
    return jsonify(success=True)

@app.route('/remove_word', methods=['POST'])
def remove_word():
    data = request.get_json()
    index = data['index']
    if 'words' in session:
        wordlist = session['words']
        wordlist.pop(index)
        session['words'] = wordlist
    return jsonify(success=True)

@app.route('/add_word', methods=['POST'])
def add_word():
    data = request.get_json()
    word = data['word']
    if 'words' not in session:
        session['words'] = [word]
    else:
        wordlist = session['word']
        wordlist.append(word)
        session['word'] = wordlist
    return jsonify(success=True)

@app.route('/export_rules')
def export_rules():
    output = '\n'.join(session['rules'])
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=phonological_rules.csv"})


@app.route('/move_down', methods=['POST'])
def move_down():
    data = request.get_json()
    index = data['index']
    ruleset = session['rules']
    if index < len(ruleset) - 1:  # Ensure there is a next element to swap with
        ruleset[index], ruleset[index + 1] = ruleset[index + 1], ruleset[index]
        session['rules'] = ruleset
        return jsonify(message="Moved down successfully!")
    return jsonify(message="Move down not possible.")

@app.route('/move_up', methods=['POST'])
def move_up():
    data = request.get_json()
    index = data['index']
    ruleset = session['rules']
    if index > 0:  # Ensure there is a previous element to swap with
        ruleset[index], ruleset[index - 1] = ruleset[index - 1], ruleset[index]
        session['rules'] = ruleset
        return jsonify(message="Moved up successfully!")
    return jsonify(message="Move up not possible.")

@app.route('/export_csv')
def export_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Input', 'Output', 'Rules Applied'])
    if 'rules_table' in session:
        for entry in session['rules_table']:
            cw.writerow([entry['word'], entry['result'], entry['rules_applied']])

    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                     "attachment; filename=rule_application.csv"})


@app.route('/clear_session')
def clear_session():
    print('clearing session rules: ', session['rules'])
    session['rules'] = list()
    session['words'] = list()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run()