from flask import Flask, render_template, request, flash, redirect, session, jsonify, Response
from werkzeug.datastructures import Headers
from werkzeug.utils import secure_filename
import numpy as np
import json
from flask_session import Session
from sklearn import preprocessing
from sklearn.decomposition import PCA
import pickle
import helpers
from pymcr.mcr import McrAR
from pymcr.regressors import OLS, NNLS
from pymcr.constraints import ConstraintNonneg, ConstraintNorm

app = Flask(__name__)
app.secret_key = 'W^4\xf3\x02\xb4\xf5\r\xbd\x9b\x99\x17\xf4Zp\xf5\xfe\x9f\xf1\xc1\xdc\xd5\xdf.'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_spectral_data', methods=['GET', 'POST'])
def get_spectral_data():
    if request.method == 'POST':
        data = []
        wavelengths = []
        timestamps = []
        file_list = request.files.getlist('file')
        print('Success')
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
            timestamps.append(helpers.to_seconds(column.pop(0)))    
        wavelengths.pop(0) #Removes first entry which is the title "Wavelengths"
        with open('arrayfile', 'wb') as outfile:
            pickle.dump(data, outfile)
        with open('wavelengths', 'wb') as outfile:
            pickle.dump(wavelengths, outfile)
        with open('timestamps', 'wb') as outfile:
            pickle.dump(timestamps, outfile)
        returnfile = {'data': data, 'wavelengths': wavelengths, 'timestamps': timestamps}
        return jsonify(returnfile)

@app.route('/update_wavelength/', methods=['GET'])
def update_wavelength():
    [wavelength_low, wavelength_high] = [int(request.args.get('wavelength_low')), int(request.args.get('wavelength_high'))]
    session['wavelength_low'] = wavelength_low
    session['wavelength_high'] = wavelength_high
    return 'Success'

@app.route('/update_time/', methods=['GET', 'POST'])
def update_time():
    [time_low, time_high] = [int(request.args.get('time_low')), int(request.args.get('time_high'))]
    print(time_low)
    session['time_low'] = time_low
    session['time_high'] = time_high
    return 'Success'

@app.route('/compute_pca', methods=['GET', 'POST'])
def compute_pca():
    n = int(request.data.decode("utf-8"))
    with open('arrayfile', 'rb') as infile:
        array = pickle.load(infile)
    with open('wavelengths', 'rb') as infile:
        wavelengths = pickle.load(infile)
    with open('timestamps', 'rb') as infile:
        timestamps = pickle.load(infile)
    
    wavelength_low_index = helpers.find_low_index(wavelengths, session['wavelength_low'])
    wavelength_high_index = helpers.find_high_index(wavelengths, session['wavelength_high'])
    time_low_index = helpers.find_low_index(timestamps, session['time_low'])
    time_high_index = helpers.find_high_index(timestamps, session['time_high'])

    newarray = []
    for column in array[time_low_index : time_high_index]:
        newarray.append(column[wavelength_low_index : wavelength_high_index])

    array1 = preprocessing.normalize(newarray)
    pca = PCA(n_components = n)
    pca.fit_transform(array1)
    with open('compfile', 'wb') as outfile:
        pickle.dump(pca.components_.tolist(), outfile)
    returnfile = {'index': [], 'variance': []}
    
    for index, variance in enumerate(pca.explained_variance_ratio_.tolist()):
        returnfile['index'].append(index + 1)
        returnfile['variance'].append(variance * 100)
    with open('pca_data', 'wb') as outfile:
        pickle.dump(returnfile, outfile)
    return jsonify(returnfile)

@app.route('/compute_mcr', methods=['GET', 'POST'])
def compute_mcr():
    n = int(request.data.decode("utf-8"))
    with open('arrayfile', 'rb') as infile:
        array = pickle.load(infile)
    with open('wavelengths', 'rb') as infile:
        wavelengths = pickle.load(infile)
    with open('timestamps', 'rb') as infile:
        timestamps = pickle.load(infile)
    with open('compfile', 'rb') as infile:
        components = pickle.load(infile)
    
    wavelength_low_index = helpers.find_low_index(wavelengths, session['wavelength_low'])
    wavelength_high_index = helpers.find_high_index(wavelengths, session['wavelength_high'])
    time_low_index = helpers.find_low_index(timestamps, session['time_low'])
    time_high_index = helpers.find_high_index(timestamps, session['time_high'])

    newarray = []
    for column in array[time_low_index : time_high_index]:
        newarray.append(column[wavelength_low_index : wavelength_high_index])
        
    n = int(request.data.decode("utf-8"))
    
    mcrar = McrAR(max_iter=100, st_regr='NNLS', c_regr=OLS(), c_constraints=[ConstraintNonneg()])
    mcrar.fit(np.array(newarray, float), ST=np.array(components[:n], float), verbose=True)
    print("MCRAR successful")
    spectra = mcrar.ST_opt_.tolist()
    concentration = np.transpose(mcrar.C_opt_).tolist()
    wavelengths = wavelengths[wavelength_low_index:wavelength_high_index]
    returnfile = {'concentration': concentration, 'timestamps': timestamps, 'spectra': spectra, 'wavelengths': wavelengths}
    return jsonify(returnfile)

@app.route("/download_pca", methods=['GET'])
def download_pca():
    with open('pca_data', 'rb') as infile:
        pca_data = pickle.load(infile)
    excel_data = helpers.download_excel(pca_data)
    headers = Headers()
    headers.set("Content-Disposition", "attachment", filename = 'PCA.xlsx')
    return Response(excel_data, mimetype = "application/vnd.ms-excel", headers=headers)
    
if __name__=='__main__':
    app.run(debug=True)