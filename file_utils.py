import os, yaml, scipy.io, pickle, csv
from PyQt5 import QtGui


def dict2yaml(expt_dict, filename='exp_params.yaml'):
    with open(filename, 'w') as outfile:
        outfile.write(yaml.dump(expt_dict, default_flow_style=False))


def yaml2dict(filename='exp_params.yaml'):

    data = {}
    with open(filename, 'r') as infile:
        try:
            data = yaml.load(infile)
        except yaml.YAMLError as exc:
            print(exc)

    if data != {}:
        return data
    else:
        raise ImportError


def save_data(filename, data, graph=None, fig=None, sweep_params=None, remotedir=r'Y:\Data\Confocal1',tracker_tab = None):
    if os.path.exists(remotedir):
        saveremote = True
    else:
        saveremote = False
    saveremote = False # TODO: uncomment this later

    if True:
        scipy.io.savemat(os.path.expanduser(os.path.join('~', 'Documents', 'data_mat', filename+'.mat')), mdict=data)
        if saveremote:
            scipy.io.savemat(os.path.expanduser(os.path.join(remotedir, 'data_mat', filename + '.mat')),
                             mdict=data)
    if graph is not None:
        graph.save(os.path.expanduser(os.path.join('~', 'Documents', 'graphs_mat', '%s.png' % filename)), 'png')
        if saveremote:
            graph.save(os.path.expanduser(os.path.join(remotedir, 'graphs_mat', '%s.png' % filename)), 'png')

    if fig is not None:
        fig.save(os.path.expanduser(os.path.join('~', 'Documents', 'figs_mat', '%s.png' % filename)), 'png')
        if saveremote:
            fig.save(os.path.expanduser(os.path.join(remotedir, 'figs_mat', '%s.png' % filename)), 'png')
    if sweep_params is not None:
        dict2yaml(sweep_params, os.path.expanduser(os.path.join('~', 'Documents', 'data_mat', '%s.yaml' % filename)))
        if saveremote:
            dict2yaml(sweep_params,
                      os.path.expanduser(os.path.join(remotedir, 'data_mat', '%s.yaml' % filename)))

    # if tracker_tab is not None:
    #     tracker_tab.save(os.path.expanduser(os.path.join('~', 'Documents', 'figs_mat', '%s.png' % filename)), 'png')

def savemat(path, data):
    scipy.io.savemat(path, mdict=data)


def getwavenum():
    eppath = os.path.expanduser(os.path.join('~', 'Documents', 'data_mat'))
    # filelist = [f for f in os.listdir(eppath) if os.path.isfile(os.path.join(eppath, f))]
    filelist = [f for f in os.listdir(eppath)] # to speed up
    numlist = []
    for f in filelist:
        if '.mat' in f:
            filename = f.split('.mat')[0]
            numlist.extend([int(s) for s in filename.split('_') if s.isdigit()])

    if not numlist:
        return 0
    else:
        return max(numlist)


def save_config(configsettings, path='.'):
    '''save gui settings which are passed in as dictionary, configsettings'''
    filename = 'guisettings.config'
    fullpath = os.path.join(path, filename)
    pickle.dump(configsettings, open(fullpath, 'wb'))


def load_config(fullpath='./guisettings.config'):
    '''load settings for the gui and populate it'''
    data = pickle.load(open(fullpath,'rb'))
    return data


def table2csv(qtable, filename):
    numrows = qtable.rowCount()

    with open(filename, 'wt', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in range(numrows):
            row2write = []
            for col in range(qtable.columnCount()):
                item = qtable.item(row, col)
                if item is None:
                    row2write.append('')
                else:
                    row2write.append(item.text())

            writer.writerow(iter(row2write))


def csv2table(qtable, filename):
    with open(filename, 'rt', newline='') as csvfile:
        reader = csv.reader(csvfile)

        table = [data for data in reader]

        numrows = len(table)
        qtable.setRowCount(numrows)

        for row in range(len(table)):
            for col in range(len(table[row])):
                qtable.setItem(row, col, QtGui.QTableWidgetItem(table[row][col]))
