import os
from scipy.io import loadmat
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from datasets.SequenceDatasets import dataset
from datasets.sequence_aug import *
from tqdm import tqdm


signal_size = 1024
dataname= {0:["97.mat","105.mat", "118.mat", "130.mat", "169.mat", "185.mat", "197.mat", "209.mat",],  # 1797rpm#TODO DATA
           1:["98.mat","106.mat", "119.mat", "131.mat", "170.mat", "186.mat", "198.mat", "210.mat", ],  # 1772rpm
           2:["99.mat","107.mat", "120.mat", "132.mat", "171.mat", "187.mat", "199.mat", "211.mat"],  # 1750rpm
           3:["100.mat","108.mat", "121.mat","133.mat", "172.mat", "188.mat", "200.mat", "212.mat", "225.mat","237.mat"],
           11: ["D_h.mat", "DI_h.mat", "DIO_h.mat", "DO_h.mat", "LI_h.mat", "LO_h.mat", 'LIO_h.mat', "L_h.mat"],
           # "D_h.mat","DI_h.mat", "DIO_h.mat","DO_h.mat","LI_h.mat",,"LI_h.mat","LIO_h.mat","LO_h.mat"
           10: ["D_hb.mat", "DI_hb.mat", "DIO_hb.mat", "DO_hb.mat", "LI_hb.mat", "LO_hb.mat", 'LIO_hb.mat', 'L_hb.mat'],
           # "D_hb.mat","DI_hb.mat", "DIO_hb.mat","DO_hb.mat","LI_hb.mat",,"LI_hb.mat","LIO_hb.mat","LO_hb.mat"
           12: ["D_h.mat", "DI_h.mat", "DIO_h.mat", "DO_h.mat"],
           13: ["D_hb.mat", "DI_hb.mat", "DIO_hb.mat", "DO_hb.mat"],
           6: ["nz.mat", "iz.mat", "oz.mat", "rz.mat"],  # 株洲z
           7
           : ["nc.mat", "ic.mat", "oc.mat", "rc.mat"],  # 西储c
           # 8: ["nk24.mat","ik24.mat", "ok24.mat","rk24.mat"],#鲲鹏k
           8: ["15nk24.mat", "15ik24.mat", "15ok24.mat", "15gk24.mat"],  # 鲲鹏k
           9: ["np.mat", "ip.mat", "op.mat", "rp.mat"],  # 泵
           14: ["nj.mat", "ij.mat", "oj.mat", "rj.mat"]}  # 江南 # 1730rpm

datasetname = ["12k Drive End Bearing Fault Data", "12k Fan End Bearing Fault Data", "48k Drive End Bearing Fault Data",
               "Normal Baseline Data"]
axis = ["_DE_time", "_FE_time", "_BA_time"]

label = [i for i in range(0, 8)]#TODO num(1)

def get_files(root, N):
    data = []
    lab =[]
    for k in range(len(N)):
        for n in tqdm(range(len(dataname[N[k]]))):
            if n==0:
               path1 =os.path.join(root,datasetname[3], dataname[N[k]][n])
            else:
                path1 = os.path.join(root,datasetname[0], dataname[N[k]][n])
            data1, lab1 = data_load(path1,dataname[N[k]][n],label=label[n])
            data += data1
            lab +=lab1

    return [data, lab]


def data_load(filename, axisname, label):
    datanumber = axisname.split(".")
    if eval(datanumber[0]) < 100:
        realaxis = "X0" + datanumber[0] + axis[0]
    else:
        realaxis = "X" + datanumber[0] + axis[0]
    fl = loadmat(filename)[realaxis]
    #fl = (fl - fl.mean()) / fl.std()
    data = []
    lab = []
    start, end = 0, signal_size
    while end <= 102400:
        data.append(fl[start:end])
        lab.append(label)
        start += signal_size
        end += signal_size
    return data, lab

def get_filesz(root, N):
    data = []
    lab =[]
    for k in range(len(N)):
        for n in tqdm(range(len(dataname[N[k]]))):
            path1 = os.path.join(root, dataname[N[k]][n])
            data1, lab1 = data_loadz(path1,dataname[N[k]][n],label=label[n])
            data += data1
            lab +=lab1

    return [data, lab]
def data_loadz(filename, axisname, label):
    fl = loadmat(filename)['z']
    # fl = (fl-fl.min())/(fl.max()-fl.min())+-1 #-1-1
    #fl = (fl-fl.mean())/fl.std()
    data = []
    lab = []
    start, end = 0, signal_size
    while end <= 102400:#121200
        data.append(fl[start:end])
        lab.append(label)
        start += signal_size
        end += signal_size
    return data, lab
#--------------------------------------------------------------------------------------------------------------------
class CWRU(object):
    num_classes = 8#TODO num(2)
    inputchannel = 1
    def __init__(self, data_dir, transfer_task, normlizetype="0-1"):
        self.data_dir = data_dir
        self.source_N = transfer_task[0]
        self.target_N = transfer_task[1]
        self.normlizetype = normlizetype
        self.data_transforms = {
            'train': Compose([
                Reshape(),
                Normalize(self.normlizetype),
                # RandomAddGaussian(),
                # RandomScale(),
                # RandomStretch(),
                # RandomCrop(),
                Retype(),
                # Scale(1)
            ]),
            'val': Compose([
                Reshape(),
                Normalize(self.normlizetype),
                Retype(),
                # Scale(1)
            ])
        }

    def data_split(self, transfer_learning=True):
        if transfer_learning:

            list_data = get_files(self.data_dir, self.source_N)#TODO get_files
            data_pd = pd.DataFrame({"data": list_data[0], "label": list_data[1]})
            train_pd, val_pd = train_test_split(data_pd, test_size=0.2, random_state=40, stratify=data_pd["label"])
            source_train = dataset(list_data=train_pd, transform=self.data_transforms['train'])
            source_val = dataset(list_data=val_pd, transform=self.data_transforms['val'])

            list_data = get_files(self.data_dir, self.target_N)
            data_pd = pd.DataFrame({"data": list_data[0], "label": list_data[1]})
            train_pd, val_pd = train_test_split(data_pd, test_size=0.2, random_state=40, stratify=data_pd["label"])
            target_train = dataset(list_data=train_pd, transform=self.data_transforms['train'])
            target_val = dataset(list_data=val_pd, transform=self.data_transforms['val'])
            return source_train, source_val, target_train, target_val
