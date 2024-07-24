import pandas as pd

def read_target_data(filepath):
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
        data = pd.DataFrame([list(map(float, filter(None, line.split(',')))) for line in data_lines])
        time_data = data.iloc[:, 0::2]
        value_data = data.iloc[:, 1::2]
    else:
        time_data = pd.DataFrame()
        value_data = pd.DataFrame()

    return time_data, value_data, variable_names, header_lines

def export_for_plotjuggler(time_data, value_data, variable_names, output_filepath):
    export_data = pd.DataFrame()

    for i, name in enumerate(variable_names):
        export_data[f'{name}_Time'] = time_data.iloc[:, i]
        export_data[f'{name}_Value'] = value_data.iloc[:, i]

    export_data.to_csv(output_filepath, index=False)
    print(f"Data exported to {output_filepath} for PlotJuggler.")

def process_and_export_data(input_filepath, output_filepath):
    time_data, value_data, variable_names, _ = read_target_data(input_filepath)
    export_for_plotjuggler(time_data, value_data, variable_names, output_filepath)

if __name__ == "__main__":
    input_filepath = 'exampleTrace.csv'
    output_filepath = 'output_file.csv'
    process_and_export_data(input_filepath, output_filepath)