# -*- coding: utf-8 -*-
from __future__ import print_function
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp
import warnings
import locale
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.cbook
matplotlib.use('Agg')

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def setDataModel(dataraw):
    data = {}
    weights = [w for w,_ in dataraw]
    label = [l for _,l in dataraw]
    data['weights'] = weights
    data['label'] = label
    data['items'] = list(range(len(weights)))
    data['bins'] = list(range(300))
    data['bin_capacity'] = 5800
    return data


def solveLinearCut5(data):
    solver = pywraplp.Solver.CreateSolver('SCIP')
    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in data['items']:
        for j in data['bins']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in data['bins']:
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['bins']) == 1)

    # The amount packed in each bin cannot exceed its capacity.
    for j in data['bins']:
        solver.Add(
            sum(x[(i, j)] * (data['weights'][i]+30) for i in data['items']) <= y[j] *
            data['bin_capacity'])

    # Objective: minimize the number of bins used.
    if sum(x[i,j] * data['weights'][i] for i in data['items'] for j in data['bins']) <= 5800*7 :
        solver.Minimize(sum([y[j] for j in data['bins']]))
    
    status = solver.Solve()

    res = {}

    if status == pywraplp.Solver.OPTIMAL:
        num_bins = 0
        for j in data['bins']:
            if y[j].solution_value() == 1:
                bin_items = []
                bin_weight = 0
                art_weight = 0
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        bin_items.append(i)
                        bin_weight += data['weights'][i]
                if bin_weight > 0:
                    num_bins += 1
                    res[num_bins] = {}
                    res[num_bins]['morceau'] = [(data['weights'][it],data['label'][it]) for it in bin_items]
                    res[num_bins]['used'] = bin_weight
                    res[num_bins]['chute'] = data['bin_capacity'] - bin_weight
    else:
        print('The problem does not have an optimal solution.')
    return res

def afficheSol(res):
    if len(res) > 0:
        with PdfPages('Impression.pdf') as pdf:
            # A4 canvas
            fig_width_cm = 21
            fig_height_cm = 9.5
            inches_per_cm = 1 / 2.54
            fig_width = fig_width_cm * inches_per_cm
            fig_height = fig_height_cm * inches_per_cm
            fig_size = [fig_width, fig_height]

            for i in res:
                fig = plt.figure()
                fig.set_size_inches(fig_size)
                fig.patch.set_facecolor('#FFFFFF')
                ax = fig.add_subplot()
                ax.invert_yaxis()
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)
                ax.set_xlim(0, 5800)
                ax.set_ylim(0, 3)
                ax.set_facecolor('#FFFFFF')
                t = 1
                start = 0
                ax.barh(str(t), 5800, left=start, height=0.5, Fill=None, hatch='///')
                for j in res[i]['morceau']:
                    ax.barh(str(t), j[0], left=start, height=0.5, label=str(j[0]) + ' : ' + j[1])
                    ax.text(start + (j[0] / 2), t - 1, j[0], ha='center', va='bottom',
                            color='#000000')
                    start += j[0]
                    t = 1
                plt.legend(loc='upper left',
                           ncol=1, mode="expand", borderaxespad=0.)
                pdf.savefig(dpi=300, orientation='portarit')
                plt.close()

    print(' | Nombre de barres utilise:', len(res))

if __name__ == '__main__':
    test = [(3000,'01'),(2500,'02'),(1200,'03'),(1500,'04'),(2100,'05'),(3200,'06'),(1000,'07'),(900,'08'),(1400,'09')]
    data = setDataModel(test)
    res = solveLinearCut5(data)
    afficheSol(res)
