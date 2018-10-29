"""
Generate state evolution overview plots for UCLALES simulations
"""
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

import os

import numpy as np
import matplotlib.pyplot as plot
from matplotlib.gridspec import GridSpec
import matplotlib.font_manager

import xarray as xr

import seaborn as sns

from tqdm import tqdm

sns.set(style='ticks', color_codes=True)
sns.despine()

VARS = [
    ("zbmn", "zcmn", "zb", "zc"),
    ("lwp_bar", "rwp_bar", ),
    ("cfrac", ),
]

N_rows = len(VARS) + 1

def main(dataset_name):
    fn = os.path.join('other', '{}.ts.nc'.format(dataset_name))
    ts = xr.open_dataset(fn, decode_times=False)


    fig = plot.figure(figsize=(10, 9))

    font = matplotlib.font_manager.FontProperties()
    font.set_weight("bold")

    t = ts.time
    t_hours = t/60./60.

    t_hours_unique = np.unique(t_hours.astype(int))
    if t_hours_unique[0] == 0.:
        # nothing interesting happens right from the beginning
        t_hours_unique = t_hours_unique[1:]
    dt_step = int(t_hours_unique.max()/5)
    nt = len(t_hours_unique[::dt_step])

    for n, varset in enumerate(VARS):
        plot.subplot2grid((N_rows,nt), (n,0), colspan=nt)
        for var in varset:
            ax = plot.gca()
            plot.xlabel('time [hours]')

            data = ts[var]
            plot.plot(t_hours, data[:], label=data.longname)
            plot.ylabel('%s [%s]' % (data.longname, data.units))

            if var in ('lwp_bar', 'rwp_bar'):
                plot.ylim(0, None)
            else:
                plot.ylim(0, 1.2*data[:].max())

            plot.grid(True)
            # ticks = 240.*np.arange(0, 12)
            # plot.xticks(ticks)

        if len(varset) > 1:
            plot.legend()
        else:
            plot.title(data.longname)


    fn_3d = os.path.join('raw_data', '{}.00000000.nc'.format(dataset_name))
    if os.path.exists(fn_3d):
        data_3d = xr.open_dataset(fn_3d, decode_times=False)

        x_, y_ = data_3d.time/60./60., np.zeros_like(data_3d.time)
        plot.plot(x_, y_, marker='o', linestyle='', color='red')

        for tn_, (x__, y__) in enumerate(zip(x_, y_)):
            ax.annotate(
                tn_, xy=(x__, y__),
                xytext=(0, 10), color='red',
                textcoords='offset pixels',
                horizontalalignment='center', verticalalignment='bottom'
            )

    fn = os.path.join(
        'cross_sections', 'runtime_slices',
        '{}.out.xy.lwp.nc'.format(dataset_name)
    )

    if not os.path.exists(fn):
        raise Exception("Can't find `{}`, needed for overview plots"
                        "".format(fn))
    da = xr.open_dataarray(fn, decode_times=False)

    if not da.time.units.startswith('seconds'):
        raise Exception("The `{}` has the incorrect time units (should be"
                        " seconds) which is likely because cdo mangled it."
                        " Recreate the file making sure that cdo is explicitly"
                        " told to use a *relative* time axis. The current"
                        " units are `{}`.".format(fn, da.time.units))

    for n, t_ in enumerate(tqdm(t_hours_unique[::dt_step])):
        plot.subplot2grid((N_rows, nt), (N_rows-1, n))

        d = da.sel(
            time=t_*60.*60., drop=True, tolerance=5.*60., method='nearest'
        )

        x, y = da.xt, da.yt

        has_units = hasattr(x, 'units') and hasattr(y, 'units')

        s = 1.0
        if has_units and x.units == 'm' and y.units == 'm':
            s = 1.0e-3
            units = 'km'
            assert x.units == y.units
        else:
            units = None

        plot.pcolormesh(
            x, y, d > 0.001,
            cmap=plot.get_cmap('Greys_r'),
            rasterized=True
        )

        if has_units:
            plot.xlabel('horizontal dist. [{}]'.format(units))
            if n == 0:
                plot.ylabel('horizontal dist. [{}]'.format(units))

        plot.title('t={}hrs'.format(t_))
        plot.gca().set_aspect(1)


if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser(__doc__)
    argparser.add_argument('--filetype', default='pdf')
    args = argparser.parse_args()

    import glob
    files = glob.glob('other/*.ts.nc')
    if len(files) == 0:
        raise Exception("Can't find *.ts.nc file, needed for this plot")
    dataset_name = os.path.basename(files[0]).split('.')[0]

    print("Plotting evolution for `{}`".format(dataset_name))

    main(dataset_name)

    plot.tight_layout()
    plot.savefig("{}.evolution.{}".format(dataset_name, args.filetype))
