import numpy as n
import matplotlib
from matplotlib.pyplot import *
import datetime

def timeTicks(x, pos):
    d = datetime.timedelta(seconds=x)
    return str(d)


def plot_trackers(sat, smoothing_window=50.0, clip_ends=True):

    formatter = matplotlib.ticker.FuncFormatter(timeTicks)

    # need this so the plots make sense
    smoothing_kernel = n.ones(int(smoothing_window))/smoothing_window

    times = sat.trackers['time']
    start = int(smoothing_window) if clip_ends else 0
    end = len(times) - int(smoothing_window) if clip_ends else len(times)

    fig = figure(figsize=(12, 30))
    ax1 = subplot(5, 1, 1)
    n_loads = len(sat.trackers['loads'][0].keys())
    added_height = 2 * n_loads - 2
    locs = []
    labels = []
    for load in sat.trackers['loads'][0].keys():
        plot(times[start:end], n.convolve([added_height + int(l[load][0])
                                for l in sat.trackers['loads']], smoothing_kernel, mode='same')[start:end], label=load)
        locs.append(added_height+0.5)
        labels.append(load)
        added_height -= 2
    yticks(locs, labels)
    # legend()
    ylim(-0.2, 0.2 + 2*n_loads)
    title('ON/OFF State of Loads')
    # ylabel('Duty Cycle of Load')
    xlabel("Time from launch (hh:mm:ss)")

    ax1.xaxis.set_major_formatter(formatter)

    ax1 = subplot(5, 1, 2)
    ax1.plot(times[start:end], [s['structure']
                                for s in sat.trackers['temperatures']][start:end], label='Structure Temp (K)')
    ax1.plot(times[start:end], [s['payload']
                                for s in sat.trackers['temperatures']][start:end], label='Payload Temp (K)')
    ax1.plot(times[start:end], [s['battery']
                                for s in sat.trackers['temperatures']][start:end], label='Battery Temp (K)')
    legend()
    title('Temperatures')
    xlabel("Time from launch (hh:mm:ss)")
    ylabel('Temperature (K)')
    ax1.xaxis.set_major_formatter(formatter)

    ax2 = subplot(5, 1, 3)
    ax2.plot(times[start:end], [s['structure']
                                for s in sat.trackers['qdots']][start:end], label='Structure Qdot (K)')
    ax2.plot(times[start:end], n.convolve([s['payload'] for s in sat.trackers['qdots']],
                                          smoothing_kernel, mode='same')[start:end], label='Payload Qdot (K)')
    ax2.plot(times[start:end], n.convolve([s['battery'] for s in sat.trackers['qdots']],
                                          smoothing_kernel, mode='same')[start:end], label='Battery Qdot (K)')
    legend()
    title('Instantenous Heat Transfer')
    xlabel("Time from launch (hh:mm:ss)")
    ylabel('Qdot (W)')
    ax2.xaxis.set_major_formatter(formatter)

    ax1 = subplot(5,1,4)
    ax1.plot(times[start:end], n.convolve(sat.trackers['power_in'], smoothing_kernel, mode='same')[start:end], label='Power Generated', color='g')
    ax1.plot(times[start:end], n.convolve(sat.trackers['power_out'], smoothing_kernel, mode='same')[start:end], label='Power Consumed', color='r')
    ax1.plot(times[start:end], n.convolve(sat.trackers['power_net'], smoothing_kernel, mode='same')[start:end], label='Net Power', color='b')
    ax1.xaxis.set_major_formatter(formatter)
    xlabel("Time from launch (hh:mm:ss)")
    ax1.set_ylabel("Power (mW)")
    legend()
    title('Power Consumed and Generated')

    ax1 = subplot(5, 1, 5)
    ax2 = ax1.twinx()
    l1 = ax1.plot(times[start:end], sat.trackers['batt_v'][start:end],
                  label='Battery Voltage', color='b')
    # l2 = ax2.plot(times[start:end], n.convolve(
    #     sat.trackers['batt_current_out'], smoothing_kernel, mode='same')[start:end], label='Battery Current (out)', color='r')
    # l3 = ax2.plot(times[start:end], n.convolve(
    #     sat.trackers['batt_current_in'], smoothing_kernel, mode='same')[start:end], label='Battery Current (in)', color='g')
    ax1.xaxis.set_major_formatter(formatter)
    # ax2.xaxis.set_major_formatter(formatter)
    xlabel("Time from launch (hh:mm:ss)")
    ax1.set_ylabel("Voltage (V)")
    # ax2.set_ylabel("Current (mA)")

    lines = l1  # +l2+l3
    legend(lines, [l.get_label() for l in lines])
    title('Battery Status')
    return fig
