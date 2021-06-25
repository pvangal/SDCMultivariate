import io
import xlsxwriter
import pickle
import numpy as np

def readIR(file_list, data, wavelengths, timestamps):
    for file in file_list:
        file_contents = file.stream.read().decode("utf-8")
        data.append([])
        csvfile = file_contents.split('\n')
        csvfile.pop()
        if wavelengths == []:
            for row in csvfile:
                try:
                    data[-1].append(float(row.split(',')[1].strip()))
                    wavelengths.append(float(row.split(',')[0].strip()))
                except:
                    data[-1].append(row.split(',')[1].strip())
                    wavelengths.append(row.split(',')[0].strip())
        else:
            for row in csvfile:
                try:
                    data[-1].append(float(row.split(',')[1].strip()))
                except:
                    data[-1].append(row.split(',')[1].strip())
    for column in data:
        timestamps.append(to_seconds(column.pop(0)))
        column.reverse()  
    start_time = timestamps[0]
    for index in range(len(timestamps)):
        timestamps[index] = timestamps[index] - start_time
    wavelengths.pop(0) #Removes first entry which is the title "Wavelengths"
    wavelengths.reverse()
    with open('arrayfile', 'wb') as outfile:
        pickle.dump(data, outfile)
    with open('wavelengths', 'wb') as outfile:
        pickle.dump(wavelengths, outfile)
    with open('timestamps', 'wb') as outfile:
        pickle.dump(timestamps, outfile)

def readRaman(file_list, data, wavelengths, timestamps):
    for file in file_list:
        file_contents = file.stream.read().decode("utf-8")
    csvfile = file_contents.split('\n')
    print (len(csvfile))
    csvfile.pop(-1)
    for row in csvfile:
        data.append([float(entry.rstrip()) for entry in row.split(',')])
    data.pop(0)
    wavelengths = [entry for entry in range(0, len(data), 1)] 
    timestamps = [entry for entry in range(0, len(data[0]), 1)]
    print("Shape of array being stored into pickle")
    print(np.array(data).shape)
    with open('arrayfile', 'wb') as outfile:
        pickle.dump(data, outfile)
    with open('wavelengths', 'wb') as outfile:
        pickle.dump(wavelengths, outfile)
    with open('timestamps', 'wb') as outfile:
        pickle.dump(timestamps, outfile)

def find_low_index(listname, entry):
    index = 0
    while (True and index < (len(listname) - 1)):
        if int(listname[index]) > entry:
            return index
        index += 1

def find_high_index(listname, entry):
    index = 0
    while (True and index < len(listname)):
        if int(listname[index]) > entry:
            return index-1
        index += 1
    return len(listname)

def to_seconds(timestamp):
    [hours, minutes, seconds] = [float(entry) for entry in timestamp.split(':')]
    time_in_seconds = hours*3600 + minutes*60 + seconds
    return time_in_seconds

def download_excel(data_dict): 
    io_handle = io.BytesIO()
    data = []
    for key in data_dict:
        data.append([]) 
        data[-1].append(key)
        for entry in data_dict[key]:
            if (type(entry) is list):
                for datum in entry:
                    data[-1].append(datum) 
            data[-1].append(entry) 
    print("this is data in download_excel")
    print(data)
    worksheet_columns = [] 
    worksheet_columns.append(data[0])
    
    #Skip the first column 

    charts = [] 
    for i, col in enumerate(data[1:len(data)]):
        worksheet_columns.append(col) 
        chart_metadata = {"x_axis" : 'A', "y_axis":
        [index_to_letter(i + 2)], "series_name":  [col[0]], "x_axis_name" :
        data[0][0] , "y_axis_name" : col[0] } 
        charts.append(chart_metadata)  
        
    io_handle = io.BytesIO()
    io_handle  = make_workbook(io_handle, worksheet_columns, charts) 
    
    return io_handle.getvalue()

def index_to_letter(n): 
    """
        Covert the column index to the alphabetic index 
        excel uses 
        Examples: 
            A = 1 
            Z = 26 
            AA = 27 
    """
    
    res = ""

    while n > 0:

        # find index of next letter and concatenate the letter
        # to the solution

        # Here index 0 corresponds to 'A' and 25 corresponds to 'Z'
        index = (n - 1) % 26
        res += chr(index + ord('A'))
        n = (n - 1) // 26

    return res[::-1]

def make_workbook(io_handle,  data, charts, chart_padding =(1, 16)  ):
  
    """"
        Since we are using constant memory mode we have to write data as rows 
        Constant memory mode helps generate larger files 
        https://xlsxwriter.readthedocs.io/working_with_memory.html#memory-perf
    """
    workbook = xlsxwriter.Workbook(io_handle,  {'strings_to_numbers':
    True , "constant_memory" : True}) 

    worksheet = workbook.add_worksheet()
    row_counter = 0 
    while row_counter < len(data[0]):
        row = [] 
        for col in data: 
            if row_counter < len(col):
                row.append(col[row_counter])
            else:
                #Spacer so data is misalinged
                row.append("") 
        worksheet.write_row(row_counter, 0, row)
        row_counter += 1 
    width = len(data) 
    height = len(data[0])
    for i, chart in enumerate(charts): 
        insert_loc = index_to_letter(width + chart_padding[0 ]) + str(chart_padding[1]*(i+1)) 
        worksheet.insert_chart(insert_loc, make_chart(workbook, chart,height) )

    workbook.close() 
    return io_handle 

def make_chart(workbook, chart_metadata ,data_length,  sheet_number = 1):
    """
        Organize and apply chart metadata 

        Add a series for each a given column.

    """
    chart = workbook.add_chart({"type" : "scatter" , "subtype" : "straight"}) 
    
    VALUE_STR = "={}!${}2:${}${}" 
    CAT_STR = "={}!${}$2:${}${}"

    sheet_str = "Sheet{}".format(sheet_number) 
    
    for i, series in enumerate(chart_metadata["y_axis"]):
        chart.add_series({
            "values" :
            VALUE_STR.format(sheet_str, series ,series ,data_length ),
            "categories" : CAT_STR.format(sheet_str,
            chart_metadata["x_axis"],chart_metadata["x_axis"], data_length ),
            "name" : chart_metadata["series_name"][i],
            "line" : {"width" : 1.25}
        })
    chart.set_x_axis({
        "name" : chart_metadata["x_axis_name"],
        'name_font': {'name': 'Calibri', 'color': 'black', 'bold': False},
        'num_font': {'name': 'Calibri', 'color': 'black'},
        'line': {'color': 'black'},
        'major_gridlines': {'visible': True, 'line':{'width': 1.00, 'color': '#D9D9D9'}},
        'num_font':  {'name': 'Calibri (Body)', 'size': 9},
        'name_font':  {'name': 'Calibri (Body)', 'size': 11},
        'min' : 0
    })
    
    chart.set_y_axis({
        'name': chart_metadata['y_axis_name'],
        'name_font': {'name': 'Calibri', 'color': 'black','bold': False},
        'num_font': {'name': 'Calibri', 'color':'black'},
        'line': {'color': 'black'},
        'major_gridlines': {'visible':True, 'line': {'width': 1.00,'color': '#D9D9D9'}},
        'num_font':  {'name': 'Calibri (Body)', 'size': 9},
        'name_font':  {'name': 'Calibri (Body)', 'size': 11}
    })
    chart.set_plotarea({
        'border': {'color': 'black', 'width': 0.75}
    })
    chart.set_legend({'font': {'name': 'Calibri (Body)', 'size': 12}})
    chart.set_chartarea({'border': {'none' : True}})
    chart.set_title({'none': True})
    return chart