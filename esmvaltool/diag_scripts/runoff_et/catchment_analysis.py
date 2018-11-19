#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Catchment specific water flux plots

###############################################################
runoff_et/catchment_analysis.py
Authors ESMValToolV1 Version
    Philipp Sommer (philipp.sommer@mpimet.mpg.de)
    Stefan Hagemann (stefan.hagemann@hzg.de)
    Alexander Loew
Port to ESMValTool Version 2
    Tobias Stacke (tobias.stacke@mpimet.mpg.de)
###############################################################

Description
-----------
    Plots temporal and spatial averages of precipitation, runoff and
    evaporation for specific land surface catchments. Additionally,
    relations of runoff coefficient to relative precipitation bias
    and runoff coefficient to evaporation coefficient are computed.

    Default reference data are included in this routine (default class)
    but can be replaced with other datasets. In case a custom catchment
    mask is used, the default class (catchment names, IDs, reference data)
    has to be adapted.

###############################################################

"""
import iris
import numpy as np
import calendar
import os
import logging
import pdb
import esmvaltool.diag_scripts.shared as diag
from itertools import cycle
from esmvaltool.preprocessor._regrid import regrid
from esmvaltool.preprocessor._area_pp import area_average
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(os.path.basename(__file__))


class defaults(object):
    """Class containing default dictionaries for predefined catchments

    The properties are used in the routine analysecatchments. Catchments and
    reference values are specific for the default catchment mask. All reference
    values are given in mm a-1. Precip data is based on WFDEI, runoff is based
    on GRDC, ET is derived as the difference of both. The values are updated and
    differ slightly from the ESMValTool 1 version.
    Properties are
        catchments
        mrro
        pr
        evspsbl
    """
    catchments = {
        # Catchments with name as used in make_catchment_plots and
        # associated ID used in the catchment mask netCDF file
        "Amazon": 94,
        "Parana": 98,
        "Mackenzie": 76,
        "Mississippi": 86,
        "Danube": 14,
        "Congo": 68,
        "Niger_Malanville": 65,
        "Nile": 60,
        "Lena": 40,
        "Yangtze-Kiang": 52,
        "Ganges-Brahmaputra": 54,
        "Murray": 100,
    }

    mrro = {
        'Amazon': 1194.63,
        'Congo': 365.45,
        'Danube': 250.75,
        'Ganges-Brahmaputra': 672.11,
        'Lena': 199.61,
        'Mackenzie': 173.87,
        'Mississippi': 182.12,
        'Murray': 8.20,
        'Niger_Malanville': 31.49,
        'Nile': 48.72,
        'Parana': 202.87,
        'Yangtze-Kiang': 531.33,
    }

    pr = {
        'Amazon': 2210.25,
        'Congo': 1571.41,
        'Danube': 808.04,
        'Ganges-Brahmaputra': 1405.84,
        'Lena': 387.01,
        'Mackenzie': 450.16,
        'Mississippi': 897.18,
        'Murray': 474.62,
        'Niger_Malanville': 437.90,
        'Nile': 655.62,
        'Parana': 1314.66,
        'Yangtze-Kiang': 1074.79,
    }

    evspsbl = {
        'Amazon': 1015.62,
        'Congo': 1205.96,
        'Danube': 557.29,
        'Ganges-Brahmaputra': 733.73,
        'Lena': 187.40,
        'Mackenzie': 276.29,
        'Mississippi': 715.06,
        'Murray': 466.42,
        'Niger_Malanville': 406.41,
        'Nile': 606.90,
        'Parana': 1111.80,
        'Yangtze-Kiang': 543.46,
    }


def format_coef_plot(ax):
    """ Moves axis from border to center, adapts ticks and labels accordingly
    Parameters
    ----------
    ax : object
        plot axis object
    """
    # Add infos to axis
    ax.xaxis.set_label_coords(0.5, -0.025)
    ax.yaxis.set_label_coords(-0.025, 0.5)
    # Adapt axis range to center zero
    xmax = np.ceil(
        (np.absolute(np.array(ax.get_xlim())).max() + 5) / 10.0) * 10.0 - 5.0
    ax.set_xlim(xmax * -1, xmax)
    ymax = np.ceil(
        (np.absolute(np.array(ax.get_ylim())).max() + 5) / 10.0) * 10.0 - 5.0
    ax.set_ylim(ymax * -1, ymax)
    # remove 0 from y and x axis
    for key in ['x', 'y']:
        ticks = list(getattr(ax, 'get_%sticks' % key)())
        try:
            ticks.remove(0)
        except ValueError:
            pass
        getattr(ax, 'set_%sticks' % key)(ticks)

    # Move left y-axis and bottim x-axis to centre, passing through (0,0)
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('center')
    # Eliminate upper and right axes
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    # Show ticks in the left and lower axes only
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    return ax


def write_plotdata(cfg, plotdata, catch_info, reference):
    """ Output catchment averaged values for all datasets.
    Parameters
    ----------
    cfg : dict
        Configuration dictionary of the recipe
    plotdata : dict
        Dictionary containing the catchment averages
    catch_info : object
        Object containing catchment names, IDs, and reference data
    reference : str
        String containing name of the reference dataset
    """

    ref_vars = []
    for model in plotdata.keys():
        for exp in plotdata[model].keys():
            for ens in plotdata[model][exp].keys():
                for var in plotdata[model][exp][ens].keys():
                    # Write experiment data
                    filepath = os.path.join(
                        cfg[diag.names.WORK_DIR],
                        '_'.join([var, model, exp, ens]) + '.txt')
                    with open(filepath, 'w') as f:
                        f.write(" ".join([
                            model.upper(), exp, ens, var, 'catchment averages',
                            '[mm a-1]'
                        ]) + '\n\n')
                        for river, value in sorted(
                                plotdata[model][exp][ens][var].items()):
                            f.write('{:25} : {:8.2f}\n'.format(river, value))
                    # Write reference data
                    if var not in ref_vars:
                        filepath = os.path.join(
                            cfg[diag.names.WORK_DIR],
                            '_'.join([var, 'reference']) + '.txt')
                        with open(filepath, 'w') as f:
                            f.write(" ".join([
                                'Reference', 'catchment averages', '[mm a-1]'
                            ]) + '\n\n')
                            for river, value in sorted(
                                    getattr(catch_info, var).items()):
                                f.write('{:25} : {:8.2f}\n'.format(
                                    river, value))
                        ref_vars.append(var)


def make_catchment_plots(cfg, plotdata, catch_info, reference):
    """ Plot catchment averages for precipitation, evaporation
        runoff as bar plots and relation of derived quantities.
    Parameters
    ----------
    cfg : dict
        Configuration dictionary of the recipe
    plotdata : dict
        Dictionary containing the catchment averages
    catch_info : object
        Object containing catchment names, IDs, and reference data
    reference : str
        String containing name of the reference dataset
    """
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    # Get colorscheme from recipe
    colorscheme = cfg.get('colorscheme', 'default')
    plt.style.use(colorscheme)

    for model in plotdata.keys():
        outtype = cfg.get('output_file_type', 'png')
        logger.info('Generating plots for filetype: ' + outtype)
        if outtype == 'pdf':
            filepath = os.path.join(
                cfg[diag.names.PLOT_DIR],
                model.upper() + '_runoff_et' + '.' + outtype)
            pdf = PdfPages(filepath)

        for exp in plotdata[model].keys():
            for member in plotdata[model][exp].keys():
                refdata, expdata = {}, {}

                # 1. Barplots for single variables
                for var in plotdata[model][exp][member].keys():
                    filepath = os.path.join(
                        cfg[diag.names.PLOT_DIR], '_'.join([
                            model.upper(), exp, member, 'bias-plot_' + var
                        ]) + '.' + outtype)
                    river, expdata[var], refdata[var] = [], [], []
                    for xlabel, rdata in sorted(
                            getattr(catch_info, var).items()):
                        river.append(xlabel)
                        refdata[var].append(rdata)
                        expdata[var].append(
                            plotdata[model][exp][member][var][xlabel])
                    logger.info(var + " Reference:", refdata[var])
                    logger.info(var + " Experiment:", expdata[var])

                    refdata[var], expdata[var] = np.array(
                        refdata[var]), np.array(expdata[var])
                    fig, axs = plt.subplots(nrows=1, ncols=2, sharex=False)
                    fig.suptitle(model.upper() + ' vs ' + reference.upper())
                    fig.subplots_adjust(bottom=0.35)

                    # 1a. Plot absolut bias for every catchment
                    ax = axs[0]
                    ax.set_title('\nBias for ' + var.upper())
                    ax.set_xlabel('Catchment')
                    ax.set_ylabel(var.upper() + ' [mm a-1]')
                    ax.set_xticks(range(len(river)))
                    ax.set_xticklabels((river), fontsize='small')
                    for tick in ax.get_xticklabels():
                        tick.set_rotation(90)
                    ax.bar(
                        range(len(river)),
                        expdata[var] - refdata[var],
                        color='SkyBlue')
                    ax.axhline(c='black', lw=2)

                    # 1b. Plot relative bias for every catchment
                    ax = axs[1]
                    ax.set_title('\nRelative bias for ' + var.upper())
                    ax.set_xlabel('Catchment')
                    ax.set_ylabel('Relative bias [%]')
                    ax.set_xticks(range(len(river)))
                    ax.set_xticklabels((river), fontsize='small')
                    for tick in ax.get_xticklabels():
                        tick.set_rotation(90)
                    ax.bar(
                        range(len(river)),
                        (expdata[var] - refdata[var]) / refdata[var] * 100,
                        color='IndianRed')
                    ax.axhline(c='black', lw=2)

                    plt.tight_layout()
                    if outtype == "pdf":
                        fig.savefig(pdf, dpi=80, format='pdf')
                        plt.close()
                    else:
                        fig.savefig(filepath)

                markerlist = ('s', '+', 'o', '*', 'x', 'D')
                # 2. Runoff coefficient vs relative precipitation bias
                marker = cycle(markerlist)
                filepath = os.path.join(
                    cfg[diag.names.PLOT_DIR], '_'.join([
                        model.upper(), exp, member, 'rocoef-vs-relprbias'
                    ]) + '.' + outtype)
                fig, ax = plt.subplots(nrows=1, ncols=1, sharex=False)
                for i, label in enumerate(river):
                    ax.scatter(
                        (expdata['pr'][i] - refdata['pr'][i]) /
                        refdata['pr'][i] * 100,
                        (expdata['mrro'][i] / expdata['pr'][i] * 100) -
                        (refdata['mrro'][i] / refdata['pr'][i] * 100),
                        marker=next(marker),
                        label=label)
                ax.set_title(model.upper() + ' vs ' + reference.upper())
                ax.set_xlabel('Relative bias of precipitation [%]')
                ax.set_ylabel('Bias of runoff coefficient [%]')
                ax = format_coef_plot(ax)

                fig.subplots_adjust(bottom=0.30)
                caxe = fig.add_axes([0.05, 0.01, 0.9, 0.20])
                marker = cycle(markerlist)
                for i, label in enumerate(river):
                    caxe.scatter([], [], marker=next(marker), label=label)
                caxe.legend(
                    ncol=3, numpoints=1, loc="lower center", mode="expand")
                caxe.set_axis_off()

                if outtype == "pdf":
                    fig.savefig(pdf, dpi=80, format='pdf')
                    plt.close()
                else:
                    fig.savefig(filepath)

                # 3. Runoff coefficient vs evaporation coefficient bias
                marker = cycle(markerlist)
                filepath = os.path.join(
                    cfg[diag.names.PLOT_DIR],
                    '_'.join([model.upper(), exp, member, 'rocoef-vs-etcoef'
                              ]) + '.' + outtype)
                fig, ax = plt.subplots(nrows=1, ncols=1, sharex=False)
                for i, label in enumerate(river):
                    ax.scatter(
                        (expdata['evspsbl'][i] / expdata['pr'][i] * 100) -
                        (refdata['evspsbl'][i] / refdata['pr'][i] * 100),
                        (expdata['mrro'][i] / expdata['pr'][i] * 100) -
                        (refdata['mrro'][i] / refdata['pr'][i] * 100),
                        marker=next(marker),
                        label=label)
                ax.set_title(model.upper() + ' vs ' + reference.upper())
                ax.set_xlabel('Bias of ET coefficient [%]')
                ax.set_ylabel('Bias of runoff coefficient [%]')
                ax = format_coef_plot(ax)

                fig.subplots_adjust(bottom=0.30)
                marker = cycle(markerlist)
                caxe = fig.add_axes([0.05, 0.01, 0.9, 0.20])
                for i, label in enumerate(river):
                    caxe.scatter([], [], marker=next(marker), label=label)
                caxe.legend(
                    ncol=3, numpoints=1, loc="lower center", mode="expand")
                caxe.set_axis_off()

                if outtype == "pdf":
                    fig.savefig(pdf, dpi=80, format='pdf')
                    plt.close()
                else:
                    fig.savefig(filepath)

        if outtype == "pdf":
            pdf.close()


def main(cfg):
    """Run the diagnostic.

    Parameters
    ----------
    cfg : dict
    Configuration dictionary of the recipe.
    """

    # Get dataset and variable information
    datasets = diag.Datasets(cfg)
    logging.debug("Found datasets in recipe:\n%s", datasets)
    varlist = diag.Variables(cfg)
    logging.debug("Found variables in recipe:\n%s", varlist)

    # Check for correct variables
    if not varlist.vars_available('pr', 'mrro', 'evspsbl'):
        raise ValueError(
            "Diagnostic requires precipitation, runoff and evaporation data")

    # Read catchmentmask
    # to check: Correct way to read auxillary data using recipes?
    catchment_filepath = cfg.get('catchmentmask')
    catchment_cube = iris.load_cube(catchment_filepath)
    if catchment_cube.coord('latitude').bounds is None:
        catchment_cube.coord('latitude').guess_bounds()
    if catchment_cube.coord('longitude').bounds is None:
        catchment_cube.coord('longitude').guess_bounds()
    catchment_areas = iris.analysis.cartography.area_weights(catchment_cube)

    catch_info = defaults()
    reference = 'default'

    # Read data and compute long term means
    # to check: Shouldn't this be part of preprocessing?
    # to check: How to regrid onto catchment_cube grid
    #           with preproc recipe statements
    #           instead of using regrid here?
    allcubes = {}
    plotdata = {}
    for dataset_path in datasets:
        # Prepare data dictionary
        # to check: what is a smart way to do this in python3?
        datainfo = datasets.get_dataset_info(path=dataset_path)
        dset, dexp, dens, dvar = datainfo['dataset'], datainfo[
            'exp'], datainfo['ensemble'], datainfo['short_name']
        if dset not in allcubes.keys():
            allcubes[dset] = []
        # Load data into iris cube
        new_cube = iris.load(dataset_path, varlist.standard_names())[0]
        # Check for expected unit
        if new_cube.units != 'kg m-2 s-1':
            raise ValueError('Unit [kg m-2 s-1] is expected for ',
                             new_cube.long_name.lower(), ' flux')
        # Convert to unit mm per month
        timelist = new_cube.coord('time')
        daypermonth = []
        for mydate in timelist.units.num2date(timelist.points):
            daypermonth.append(
                calendar.monthrange(mydate.year, mydate.month)[1])
        new_cube.data *= 86400.0
        for i, days in enumerate(daypermonth):
            new_cube.data[i] *= days
        # Aggregate over year --> unit mm per year
        year_cube = new_cube.aggregated_by('year', iris.analysis.SUM)
        year_cube.units = "mm a-1"
        # Compute long term mean
        mean_cube = year_cube.collapsed([diag.names.TIME], iris.analysis.MEAN)
        # Regrid to catchment data grid --> maybe use area_weighted instead?
        if mean_cube.coord('latitude').bounds is None:
            mean_cube.coord('latitude').guess_bounds()
        if mean_cube.coord('longitude').bounds is None:
            mean_cube.coord('longitude').guess_bounds()
        # mean_cube_regrid = mean_cube.regrid(catchment_cube,
        #                                     iris.analysis.Linear())
        mean_cube_regrid = mean_cube.regrid(catchment_cube,
                                            iris.analysis.AreaWeighted())
        # Get catchment area means
        rivervalues = {}
        for river, rid in catch_info.catchments.items():
            data_catch = np.ma.masked_where(
                catchment_cube.data.astype(np.int) != rid,
                mean_cube_regrid.data)
            area_catch = np.ma.masked_where(
                catchment_cube.data.astype(np.int) != rid,
                catchment_areas.data)
            rivervalues[river] = (
                data_catch * (area_catch / area_catch.sum())).sum()
        if dset == datainfo.get('reference_dataset', None):
            if reference == 'default':
                reference = datainfo['reference_dataset']
            elif reference != datainfo['reference_dataset']:
                raise ValueError(
                    'Reference must be the same for all variables!')
            setattr(catch_info, dvar, rivervalues)
        else:
            if dset not in plotdata.keys():
                plotdata[dset] = {}
            if dexp not in plotdata[dset].keys():
                plotdata[dset][dexp] = {}
            if dens not in plotdata[dset][dexp].keys():
                plotdata[dset][dexp][dens] = {}
            if dvar in plotdata[dset][dexp][dens].keys():
                raise StandardError(
                    'Variable', dvar,
                    'already exists in plot dictionary --> check script')
            else:
                plotdata[dset][dexp][dens][dvar] = rivervalues

        # Update data for dataset
        # to check: necessary at all? dataset not used later...
        datasets.set_data(mean_cube_regrid.data, dataset_path)
        # Append to cubelist for temporary output
        allcubes[dset].append(mean_cube_regrid)

    # Write regridded and temporal aggregated netCDF data files (one per model)
    # to do: update attributes
    for model in allcubes.keys():
        filepath = os.path.join(cfg[diag.names.WORK_DIR],
                                '_'.join(['postproc', model]) + '.nc')
        if cfg[diag.names.WRITE_NETCDF]:
            iris.save(allcubes[model], filepath)
            logger.info("Writing %s", filepath)

    # Write plotdata as ascii files for user information
    write_plotdata(cfg, plotdata, catch_info, reference)

    # Plot catchment data
    make_catchment_plots(cfg, plotdata, catch_info, reference)


if __name__ == '__main__':

    with diag.run_diagnostic() as config:
        main(config)
