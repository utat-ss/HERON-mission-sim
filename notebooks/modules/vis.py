import numpy as n
import matplotlib
from matplotlib.pyplot import *
import datetime

def timeTicks(x, pos):
    d = datetime.timedelta(seconds=x)
    return str(d)


def plot_trackers(sat, smoothing_window=50.0):

    formatter = matplotlib.ticker.FuncFormatter(timeTicks)

    # need this so the plots make sense
    smoothing_kernel = n.ones(int(smoothing_window))/smoothing_window

    times = sat.trackers['time']

    fig = figure(figsize=(12, 24))
    ax1 = subplot(4, 1, 1)
    n_loads = len(sat.trackers['loads'][0].keys())
    added_height = 2 * n_loads - 2
    for load in sat.trackers['loads'][0].keys():
        plot(times, n.convolve([added_height + int(l[load][0])
                                for l in sat.trackers['loads']], smoothing_kernel, mode='same'), label=load)
        added_height -= 2
    legend()
    ylim(-0.2, 0.2 + 2*n_loads)
    title('Loads')
    ylabel('Duty Cycle of Load')
    xlabel("Time from launch")

    ax1.xaxis.set_major_formatter(formatter)

    ax1 = subplot(4, 1, 2)
    ax2 = ax1.twinx()
    l1 = ax1.plot(times, sat.trackers['batt_v'],
                  label='Battery Voltage', color='b')
    l2 = ax2.plot(times, n.convolve(
        sat.trackers['batt_current_out'], smoothing_kernel, mode='same'), label='Battery Current (out)', color='r')
    l3 = ax2.plot(times, n.convolve(
        sat.trackers['batt_current_in'], smoothing_kernel, mode='same'), label='Battery Current (in)', color='g')
    ax1.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_formatter(formatter)
    xlabel("Time from launch")
    ax1.set_ylabel("Voltage (V)")
    ax2.set_ylabel("Current (mA)")

    lines = l1+l2+l3
    legend(lines, [l.get_label() for l in lines])
    title('Battery Status')

    ax1 = subplot(4, 1, 3)
    ax1.plot(times, [s['structure']
                     for s in sat.trackers['temperatures']], label='Structure Temp (K)')
    ax1.plot(times, [s['payload']
                     for s in sat.trackers['temperatures']], label='Payload Temp (K)')
    ax1.plot(times, [s['battery']
                     for s in sat.trackers['temperatures']], label='Battery Temp (K)')
    legend()
    title('Temperatures')
    xlabel("Time from launch")
    ylabel('Temperature (K)')
    ax1.xaxis.set_major_formatter(formatter)

    ax2 = subplot(4, 1, 4)
    ax2.plot(times, [s['structure']
                     for s in sat.trackers['qdots']], label='Structure Qdot (K)')
    ax2.plot(times, n.convolve([s['payload'] for s in sat.trackers['qdots']],
                               smoothing_kernel, mode='same'), label='Payload Qdot (K)')
    ax2.plot(times, n.convolve([s['battery'] for s in sat.trackers['qdots']],
                               smoothing_kernel, mode='same'), label='Battery Qdot (K)')
    legend()
    title('Qdots')
    xlabel("Time from launch")
    ylabel('Heat Transfer (W)')
    ax2.xaxis.set_major_formatter(formatter)

    return fig
