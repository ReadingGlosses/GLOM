import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import glom
import os

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def run_app():
    input_file = input_file_entry.get()
    output_file = output_file_entry.get()
    sound_changes = sound_changes_entry.get()
    if not sound_changes:
        sound_changes = None
    dictionary_dir = dictionary_dir_entry.get()
    paradigm_dir = paradigm_dir_entry.get()
    file_format = file_format_var.get()
    numbered_examples = numbered_examples_var.get()
    dictionary_order = dictionary_order_var.get().split(' ')[0].lower() # "Translation first" -> "translation"
    table_order = table_order_var.get().split(' ')[0].lower()
    input_order = input_order_var.get().split(' ')[0].lower()

    if not input_file:
        messagebox.showerror("Error", "Input file is required.")
        return

    if input_file and not output_file:
        output_file = input_file.split('.')[0]+'_glossed.txt'

    if not os.path.exists(os.path.join(os.getcwd(), input_file)):
        messagebox.showerror("File Not Found", "The input file you specified cannot be found. Double-check the spelling and make sure it is in the same folder as GLOM.")
        return

    if sound_changes:
        if not os.path.exists(os.path.join(os.getcwd(),sound_changes)):
            messagebox.showerror("File Not Found", f"The sound change file you specified cannot be found. Double-check the spelling and make sure it is in the same folder as GLOM.")
            return

    loading = ttk.Progressbar(app, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
    loading.grid(row=10, column=0, columnspan=3, pady=10)
    loading.start()

    def run_main():
        try:
            missing_data = glom.construct_examples(input_file,
                               output_file,
                               dictionary_dir=dictionary_dir,
                               paradigm_dir=paradigm_dir,
                               add_sentence_numbers=numbered_examples,
                               file_format=file_format,
                               input_order=input_order,
                               dictionary_order=dictionary_order,
                               sound_change_file=sound_changes,
                               table_order=table_order)
            message = f"Done! You can check the file {output_file} for your sentences"
            if missing_data:
                error_message = f'WARNING: The following {len(missing_data)} items in your input file could not be located in any dictionary or paradigm:\n'
                error_message += ','.join(sorted([str(m) for m in missing_data]))
                error_message += f'\nThese have been replaced by \'?\' in the output file.'
            else:
                error_message = ''
            messagebox.showinfo("Info", '\n'.join([message, error_message]))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            loading.stop()
            loading.grid_forget()

    app.after(100, run_main)



def browse_file(entry):
    filename = filedialog.askopenfilename()
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, os.path.basename(filename))

def browse_directory(entry):
    directory = filedialog.askdirectory()
    if directory:
        entry.delete(0, tk.END)
        entry.insert(0, os.path.basename(directory))

app = tk.Tk()
app.title("GLOM - A tool for generating glossed example sentences")
app.resizable(False, False)

# Input File
row = 0
input_label = tk.Label(app, text="Input File:")
input_label.grid(row=row, column=0, sticky=tk.W)
input_file_entry = tk.Entry(app, width=50)
input_file_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(app, text="Browse", command=lambda: browse_file(input_file_entry)).grid(row=0, column=2, padx=5, pady=5)
ToolTip(input_label, "Select the input file containing the sentences to work with")

# Output File
row +=1
output_label = tk.Label(app, text="Output File (just enter a name, not a full path)")
output_label.grid(row=row, column=0, sticky=tk.W)
output_file_entry = tk.Entry(app, width=50)
output_file_entry.grid(row=1, column=1, padx=5, pady=5)
ToolTip(output_label, "Type the name of an output file where glossed sentences will be printed. You can leave this blank and GLOM will create a file that has the same name as your input file, plus the suffix _glossed.")

# Sound Changes
row +=1
sound_change_label = tk.Label(app, text="Sound Changes File (optional):")
sound_change_label.grid(row=row, column=0, sticky=tk.W)
sound_changes_entry = tk.Entry(app, width=50)
sound_changes_entry.grid(row=2, column=1, padx=5, pady=5)
tk.Button(app, text="Browse", command=lambda: browse_file(sound_changes_entry)).grid(row=2, column=2, padx=5, pady=5)
ToolTip(sound_change_label, "Select a file containing sound change rules. This is optional. Consult the documentation at www.readingglosses.com/apps for details.")

# Dictionary Directory
row +=1
dictionary_dir_label = tk.Label(app, text="Dictionary Directory:")
dictionary_dir_label.grid(row=row, column=0, sticky=tk.W)
dictionary_dir_entry = tk.Entry(app, width=50)
dictionary_dir_entry.grid(row=3, column=1, padx=5, pady=5)
dictionary_dir_entry.insert(0, 'dictionaries')
tk.Button(app, text="Browse", command=lambda: browse_directory(dictionary_dir_entry)).grid(row=3, column=2, padx=5, pady=5)
ToolTip(dictionary_dir_label, "Choose the directory where all your dictionary files are located.")

# Paradigm Directory
row +=1
paradigm_dir_label = tk.Label(app, text="Paradigm Directory:")
paradigm_dir_label.grid(row=row, column=0, sticky=tk.W)
paradigm_dir_entry = tk.Entry(app, width=50)
paradigm_dir_entry.grid(row=4, column=1, padx=5, pady=5)
paradigm_dir_entry.insert(0, 'paradigms')
tk.Button(app, text="Browse", command=lambda: browse_directory(paradigm_dir_entry)).grid(row=4, column=2, padx=5, pady=5)
ToolTip(paradigm_dir_label, "Select the directory where all your paradigm files are located.")

# File Format
row +=1
file_format_label = tk.Label(app, text="Output File Format:")
file_format_label.grid(row=row, column=0, sticky=tk.W)
file_format_var = tk.StringVar(value="text")
tk.OptionMenu(app, file_format_var, "text", "pdf").grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
ToolTip(file_format_label, "Choose file type for output sentences.")

# Numbered Examples
row +=1
numbered_examples_var = tk.BooleanVar()
numbered_checkbox = tk.Checkbutton(app, text="Add numbers to the glossed sentences", variable=numbered_examples_var)
numbered_checkbox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
ToolTip(numbered_checkbox, 'Choose this option if you want sentences numbered in the output.')

# Input File Order
row +=1
input_order_label = tk.Label(app, text="Input File Order:")
input_order_label.grid(row=row, column=0, sticky=tk.W)
input_order_var = tk.StringVar(value="Translation first")
tk.OptionMenu(app, input_order_var, "Translation first", "Gloss first").grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
ToolTip(input_order_label, "Choose the order of your input file")

# Dictionary Order
row +=1
dictionary_order_label = tk.Label(app, text="Dictionary Order:")
dictionary_order_label.grid(row=row, column=0, sticky=tk.W)
dictionary_order_var = tk.StringVar(value="Gloss first")
tk.OptionMenu(app, dictionary_order_var, "Gloss first", "Morpheme first").grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
ToolTip(dictionary_order_label, "Choose the order of your dictionary file")

# Table Order
row +=1
table_order_label = tk.Label(app, text="Table Order:")
table_order_label.grid(row=row, column=0, sticky=tk.W)
table_order_var = tk.StringVar(value="Rows first")
tk.OptionMenu(app, table_order_var, "Rows first", "Columns first").grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
ToolTip(table_order_label, "Choose the order that GLOM should read your paradigm tables")

# Run Button
row +=1
tk.Button(app, text="Create sentences", command=run_app).grid(row=row, column=1, pady=10)

app.mainloop()
