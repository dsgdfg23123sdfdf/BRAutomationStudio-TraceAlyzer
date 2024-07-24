import subprocess
import sys

def install(package):
    # Install the specified Python package using pip.
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Try importing necessary packages and install them if not already installed.
try:
    import pandas as pd
except ImportError:
    install('pandas')
    import pandas as pd

try:
    import numpy as np
except ImportError:
    install('numpy')
    import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    install('matplotlib')
    import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import Tk, Checkbutton, Button, Entry, Label, IntVar, Frame, Scrollbar, VERTICAL, filedialog, LEFT, StringVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

try:
    from matplotlib.widgets import SpanSelector
except ImportError:
    install('matplotlib')
    from matplotlib.widgets import SpanSelector

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window):
        super().__init__(canvas, window)
        self.canvas = canvas
        self.window = window
        self.init_zoom_out_button()

    def zoom_out(self):
        # Zoom out functionality for the plot.
        ax = self.canvas.figure.axes[0]
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xlim([xlim[0] - 0.1 * (xlim[1] - xlim[0]), xlim[1] + 0.1 * (xlim[1] - xlim[0])])
        ax.set_ylim([ylim[0] - 0.1 * (ylim[1] - ylim[0]), ylim[1] + 0.1 * (ylim[1] - ylim[0])])
        self.canvas.draw()

    def init_zoom_out_button(self):
        # Create and add a zoom-out button to the toolbar.
        zoom_out_button = tk.Button(self, text="Zoom Out", command=self.zoom_out)
        zoom_out_button.pack(side=tk.LEFT)


connection_id = None

def read_target_data(filepath):
    # Read and extract data from the file.
    with open(filepath, 'r') as file:
        lines = file.readlines()

    variable_names = []
    data_lines = []
    header_lines = []
    reading_data = False

    for line in lines:
        line = line.strip()
        if line.startswith('%'):
            header_lines.append(line)
            if 'TARGET_DATA' in line:
                target_data_index = line.find('TARGET_DATA') + len('TARGET_DATA')
                unitx_index = line.find('XUNIT', target_data_index)
                if target_data_index != -1 and unitx_index != -1:
                    var_name = line[target_data_index:unitx_index].strip()
                    var_name = ' '.join(var_name.split())
                    variable_names.append(var_name)
                    print("Debug: Extracted variable name:", var_name)
        elif line:
            data_lines.append(line)
            reading_data = True

    if reading_data:
        # Convert data into DataFrame for easy manipulation.
        data = pd.DataFrame([list(map(float, filter(None, line.split(',')))) for line in data_lines])
        time_data = data.iloc[:, 0::2]
        value_data = data.iloc[:, 1::2]
    else:
        time_data = pd.DataFrame()
        value_data = pd.DataFrame()

    return time_data, value_data, variable_names, header_lines

def export_data(combined_data, start, end, filepath, header_lines):
    # Export the selected data to a new file.
    selected_data = combined_data.iloc[start:end+1]
    num_columns = len(combined_data.columns)
    num_pairs = num_columns // 2
    with open(filepath, 'w') as file:
        for line in header_lines:
            file.write(line + '\n')
        for index, row in selected_data.iterrows():
            line = ''
            for i in range(num_pairs):
                time_col = combined_data.columns[i]
                value_col = combined_data.columns[num_pairs + i]
                line += f"{row[time_col]},{row[value_col]},"
            file.write(line.rstrip(',') + '\n')

def plot_data(time_data, value_data, variable_names, selections, scales, offsets, colors, header_lines, fig, ax, initial=False):
    # Plot the selected data on the graph.
    print("Debug: Plotting data...")

    for color_var in colors:
        print(f"Debug: Current color value: {color_var.get()}")

    global connection_id

    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()

    ax.clear()

    lines = []
    visible_time_data = pd.DataFrame()
    visible_value_data = pd.DataFrame()

    for i, (selected, scale, offset, color_var) in enumerate(zip(selections, scales, offsets, colors)):
        if selected.get():
            print(f"Debug: Plotting variable {variable_names[i]}")
            scaled_data = value_data.iloc[:, i] * float(scale.get()) + float(offset.get())
            line, = ax.plot(time_data.iloc[:, i], scaled_data, label=variable_names[i], color=color_var.get())
            lines.append(line)
            visible_time_data = pd.concat([visible_time_data, time_data.iloc[:, i]], axis=1)
            visible_value_data = pd.concat([visible_value_data, scaled_data], axis=1)
        else:
            print(f"Debug: Skipping variable {variable_names[i]}")

    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Data Plot')
    ax.legend()
    ax.grid(True)

    # Set plot limits based on visible data
    if initial:
        if not visible_time_data.empty and not visible_value_data.empty:
            ax.set_xlim(visible_time_data.min().min(), visible_time_data.max().max())
            ax.set_ylim(visible_value_data.min().min(), visible_value_data.max().max())
    else:
        ax.set_xlim(current_xlim)
        ax.set_ylim(current_ylim)

    if not lines:
        print("Debug: No lines to plot.")

    # Cursors initialization
    cursor1 = ax.axvline(x=time_data.iloc[0, 0], color='r', linestyle='--')
    cursor2 = ax.axvline(x=time_data.iloc[0, 0], color='g', linestyle='--')
    cursor_values = {cursor1: {}, cursor2: {}}

    def on_click(event):
        # Handle mouse click event for cursor interaction.
        print("-------------Debug on_click called---------------")
        if event.inaxes != ax:
            return  # Ignore clicks outside the axes

        if event.button == 1 and event.key == 'control':  # Check if the Control key is pressed
            cursor1.set_xdata([event.xdata])
            update_cursor_values(cursor1, lines, ax, cursor_values)

        elif event.button == 3:  # Right mouse button for Cursor 2
            cursor2.set_xdata([event.xdata])
            update_cursor_values(cursor2, lines, ax, cursor_values)

        update_time_difference(cursor1, cursor2, ax)
        update_legend(lines, ax, cursor_values, cursor1, cursor2, variable_names, selections)

        fig.canvas.draw()

    global connection_id
    if connection_id is not None:
        fig.canvas.mpl_disconnect(connection_id)
    connection_id = fig.canvas.mpl_connect('button_press_event', on_click)

    fig.canvas.draw()

def update_cursor_values(cursor, lines, ax, cursor_values):
    # Update the cursor's data when clicked.
    x_pos = cursor.get_xdata()[0]
    for i, line in enumerate(lines):
        x_data = line.get_xdata()
        y_data = line.get_ydata()
        nearest_index = np.searchsorted(x_data, x_pos)
        nearest_index = min(max(nearest_index, 0), len(x_data) - 1)
        y_value = y_data[nearest_index]
        cursor_values[cursor][i] = f'{y_value:.2f}'

def update_legend(lines, ax, cursor_values, cursor1, cursor2, variable_names, selections):
    # Update the legend with the current cursor values.
    print("-------Debug update_legend called------")
    line_labels = [line.get_label() for line in lines]
    new_labels = []

    for i, line in enumerate(lines):
        value1 = cursor_values[cursor1].get(i, 'N/A')
        value2 = cursor_values[cursor2].get(i, 'N/A')
        new_label = f'{line_labels[i]}: {value1} | {value2}'
        new_labels.append(new_label)

    ax.legend(new_labels)  # Set the new legend with the updated labels

def update_time_difference(cursor1, cursor2, ax):
    # Display the time difference between the two cursors.
    x1 = cursor1.get_xdata()[0]
    x2 = cursor2.get_xdata()[0]
    time_diff = abs(x2 - x1)
    ax.set_title(f'Data Plot - Time difference: {time_diff:.2f} seconds')

def gui():
    # Initialize the GUI with tkinter.
    root = Tk()
    root.title("Signal Analyzer - Version 1.0")

    frame = Frame(root)
    frame.pack(fill='both', expand=True)

    scrollbar = Scrollbar(frame, orient=VERTICAL)
    scrollbar.pack(side='right', fill='y')

    fig, ax = plt.subplots(figsize=(10, 5))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    toolbar = CustomToolbar(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # Initialize variables and GUI elements for data.
    selections = []
    scale_entries = []
    offset_entries = []
    color_entries = []
    variable_names = []
    time_data = pd.DataFrame()
    value_data = pd.DataFrame()
    header_lines = []

    def on_change(event=None):
        # Update the plot when data changes.
        plot_data(time_data, value_data, variable_names, selections, scale_entries, offset_entries, color_entries, header_lines, fig, ax, initial=False)

    def on_change_wrapper():
        on_change()  # Calls on_change without arguments

    def export_visible_data(time_data, value_data, selections, variable_names, ax):
        # Export visible data from the plot.
        x_min, x_max = ax.get_xlim()

        for i, selected in enumerate(selections):
            if selected.get():
                time_series = time_data.iloc[:, i]
                value_series = value_data.iloc[:, i]
                mask = (time_series >= x_min) & (time_series <= x_max)
                visible_time = time_series[mask]
                visible_value = value_series[mask]

                formatted_time = f"[{', '.join(map(str, visible_time.to_numpy()))}]"
                formatted_value = f"[{', '.join(map(str, visible_value.to_numpy()))}]"

                print(f"Variable '{variable_names[i]}' Time Data:")
                print(formatted_time)
                print(f"Variable '{variable_names[i]}' Value Data:")
                print(formatted_value)
                print("\n---")  # Separation between variables

    def load_and_plot_data():
        # Load data from a file and plot it.
        nonlocal time_data, value_data, variable_names, header_lines, selections, scale_entries, offset_entries
        filepath = filedialog.askopenfilename(title="Select file", filetypes=[("CSV files", "*.csv")])
        if filepath:
            time_data, value_data, variable_names, header_lines = read_target_data(filepath)

            # Remove old GUI elements and re-create for the new variables
            for widget in frame.winfo_children():
                if isinstance(widget, Frame):
                    widget.destroy()

            selections = []
            scale_entries = []
            offset_entries = []

            color_options = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'white']
            color_index = 0

            for name in variable_names:
                var_frame = Frame(frame)
                var_frame.pack(fill='x')

                selected = IntVar(value=1)
                chk = Checkbutton(var_frame, text=name, variable=selected, command=on_change_wrapper)
                chk.pack(side='left')

                scale_label = Label(var_frame, text="Scale:")
                scale_label.pack(side='left')

                scale_entry = Entry(var_frame, width=5)
                scale_entry.insert(0, '1.0')
                scale_entry.pack(side='left')
                scale_entry.bind('<Return>', on_change)

                offset_label = Label(var_frame, text="Offset:")
                offset_label.pack(side='left')

                offset_entry = Entry(var_frame, width=5)
                offset_entry.insert(0, '0.0')
                offset_entry.pack(side='left')
                offset_entry.bind('<Return>', on_change)

                color_var = StringVar(value=color_options[color_index % len(color_options)])
                color_menu = tk.OptionMenu(var_frame, color_var, *color_options)
                color_menu.pack(side='left')

                color_var.trace_add('write', lambda *args: on_change())

                selections.append(selected)
                scale_entries.append(scale_entry)
                offset_entries.append(offset_entry)
                color_entries.append(color_var)

                color_index += 1

            plot_data(time_data, value_data, variable_names, selections, scale_entries, offset_entries, color_entries, header_lines, fig, ax, initial=True)

    # Button to load new data
    load_button = Button(root, text="Load Data", command=load_and_plot_data)
    load_button.pack()

    # Button to export visible data
    export_button = Button(root, text="Export Visible Data", command=lambda: export_visible_data(
        time_data, value_data, selections, variable_names, ax
    ))
    export_button.pack()

    root.mainloop()

if __name__ == "__main__":
    print("Welcome to Trace Analyzer Version 1.0")
    gui()
