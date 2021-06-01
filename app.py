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
from pymcr.metrics import mse

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
        if len(file_list) > 1:
            helpers.readIR(file_list, data, wavelengths, timestamps)
        else:
            helpers.readRaman(file_list, data, wavelengths, timestamps)

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
    print("shape of array being taken to preprocessing")
    print((np.array(newarray)).shape)
    array1 = preprocessing.normalize(np.transpose(newarray))
    print("shape of array after normalization")
    print(array1.shape)
    pca = PCA(n_components = n)
    components = pca.fit_transform(array1)
    print("Shape of PCA components")
    print(components.shape)
    with open('compfile', 'wb') as outfile:
        pickle.dump(components, outfile)
    returnfile = {'index': [], 'variance': []}
    
    for index, variance in enumerate(pca.explained_variance_ratio_.tolist()):
        returnfile['index'].append(index + 1)
        returnfile['variance'].append(round((variance * 100), 2))
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
    # ST_guess = []
    # for index in range(0, n):
    #     ST_guess.append([])
    #     for entry in range(0, len(components)):
    #         ST_guess[-1].append(components[entry][index])
    
    print("shape of components read in")
    print(components.shape)
    n = int(request.data.decode("utf-8"))
    components1 = components[:,:n]
    print("Shape of components1 to be used in mcrar")
    print(components1.shape)
    print("Shape of array to be fit")
    print((np.array(newarray)).shape)
   
    mcrar = McrAR(max_iter=100, st_regr='NNLS', c_regr=OLS(), c_constraints=[ConstraintNonneg()])
    mcrar.fit(np.array(newarray), ST= np.transpose(components1), verbose=True)
    print("MCRAR successful")
    spectra = mcrar.ST_opt_.tolist()
    concentration = np.transpose(mcrar.C_opt_).tolist()
    # D_calculated = mcrar.D_opt_
    # D_actual = np.array(newarray, float)
    # error = mse(mcrar.C_opt_, mcrar.ST_opt_, D_actual, D_calculated)
    # print("error is" + str(error))
    wavelengths = wavelengths[wavelength_low_index : wavelength_high_index]
    returnfile = {'concentration': concentration, 'timestamps': timestamps, 'spectra': spectra, 'wavelengths': wavelengths}
    with open('mcr_data', 'wb') as outfile:
        pickle.dump(returnfile, outfile)
    return jsonify(returnfile)

@app.route("/download_pca", methods=['GET'])
def download_pca():
    with open('pca_data', 'rb') as infile:
        pca_data = pickle.load(infile)
    excel_data = helpers.download_excel(pca_data)
    headers = Headers()
    headers.set("Content-Disposition", "attachment", filename = 'PCA.xlsx')
    return Response(excel_data, mimetype = "application/vnd.ms-excel", headers=headers)

@app.route("/download_mcr_spectra", methods=['GET'])
def download_mcr_spectra():
    with open('mcr_data', 'rb') as infile:
        saved_data = pickle.load(infile)
    
    mcr_data = {'wavelengths': saved_data['wavelengths']}
    for index, spectrum in enumerate(saved_data['spectra']):
        spectrum_name = 'spectrum' + str(index)
        mcr_data[spectrum_name] = spectrum
    excel_data = helpers.download_excel(mcr_data)
    headers = Headers()
    headers.set("Content-Disposition", "attachment", filename = 'MCR.xlsx')
    return Response(excel_data, mimetype = "application/vnd.ms-excel", headers=headers)

@app.route("/download_mcr_concentrations", methods=['GET'])
def download_mcr_concentrations():
    with open('mcr_data', 'rb') as infile:
        saved_data = pickle.load(infile)
    
    mcr_data = {'timestamps': saved_data['timestamps']}
    for index, con_profile in enumerate(saved_data['concentration']):
        profile_name = 'con_profile' + str(index)
        mcr_data[profile_name] = con_profile
    excel_data = helpers.download_excel(mcr_data)
    headers = Headers()
    headers.set("Content-Disposition", "attachment", filename = 'MCR.xlsx')
    return Response(excel_data, mimetype = "application/vnd.ms-excel", headers=headers)
    
if __name__=='__main__':
    app.run(debug=True)