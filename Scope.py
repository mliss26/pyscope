from matplotlib import style
from matplotlib.lines import Line2D
from matplotlib.ticker import AutoMinorLocator
from matplotlib.widgets import Button
from threading import Thread, Lock
from abc import ABC, abstractmethod
from colorsys import hsv_to_rgb
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import csv


class ScopeDataSource(ABC):
    '''Abstract base class for a source of data to the scope.'''

    @abstractmethod
    def __init__(self, scope, **kwargs):
        '''Data source constructor

           Must save the reference to the scope and perform any required initialization
           for the data source as well as configure the scope parameters.'''
        pass

    @abstractmethod
    def produce_data(self):
        '''Data production function

           This is where the source of data is provided to the scope. It must be a loop
           which provides one or more samples of data for every channel to the scope via
           calls to scope.add_samples.'''
        pass


class Scope(object):
    '''Oscilloscope like scrolling plot of arbitrary data.'''

    def __init__(self, refresh_ms=34, fft=False):
        self.refresh_ms = refresh_ms
        self.datasource = None
        self.datasource_thread = None
        self.datasource_running = False
        self.fft = fft

        # setup figure
        style.use('dark_background')
        if self.fft:
            self.fig, [self.axt, self.axf] = plt.subplots(2)
        else:
            self.fig, self.axt = plt.subplots()
            self.axf = None
        self.fig.canvas.manager.set_window_title('PyScope')

        self.axt.grid(True, which='major', axis='both', color='#505050')
        self.axt.grid(True, which='minor', axis='both', color='#101010')
        self.axt.xaxis.set_minor_locator(AutoMinorLocator())
        self.axt.yaxis.set_minor_locator(AutoMinorLocator())
        self.axt.set_xlabel('Time (s)')

        if self.fft:
            self.axf.set_xlabel('Frequency (Hz)')
            self.axf.set_ylabel('Magnitude (dBFS)')
            self.axf.grid(True, which='major', axis='both', color='#505050')
            self.axf.grid(True, which='minor', axis='both', color='#101010')
            self.axf.set_ylim(-180, 1)
            self.axf.xaxis.set_minor_locator(AutoMinorLocator())
            self.axf.yaxis.set_minor_locator(AutoMinorLocator())

        self.fig.tight_layout(rect=(0, 0, 1, 0.9))
        self.fig.canvas.mpl_connect('resize_event', self._on_resize)

        self.anim = animation.FuncAnimation(self.fig, self._update, self._emitter,
                interval=refresh_ms)

        # setup Run/Stop button
        self.running = False

        self.runstop = Button(plt.axes([0.8, 0.9, 0.1, 0.05]), 'Stop',
                color='#40ff40', hovercolor='#70ff70')
        self.runstop.on_clicked(self._runstop_click)
        self.runstop.label.set_color('#000000')

        # plot width zoom buttons
        self.plot_widths = [
                0.000001, 0.000002, 0.000005,
                0.000010, 0.000020, 0.000050,
                0.000100, 0.000200, 0.000500,
                0.001000, 0.002000, 0.005000,
                0.010000, 0.020000, 0.050000,
                0.100000, 0.200000, 0.500000,
                1.000000, 2.000000, 5.000000,
                10,       20,       50,
                100,      200,      500]
        self.plot_width_idx = 18 # 1 second

        self.width_next = Button(plt.axes([0.47, 0.9, 0.05, 0.05]), '-',
                color='#404040', hovercolor='#505050')
        self.width_next.on_clicked(self._width_next_click)
        self.width_next.label.set_color('#eeeeee')

        self.width_prev = Button(plt.axes([0.53, 0.9, 0.05, 0.05]), '+',
                color='#404040', hovercolor='#505050')
        self.width_prev.on_clicked(self._width_prev_click)
        self.width_prev.label.set_color('#eeeeee')

        # automatic amplitude range scale button
        self.autoscale_en = True
        self.ymax = 1
        self.ymin = 0
        self._set_ylim()

        self.autoscale = Button(plt.axes([0.125, 0.9, 0.175, 0.05]), 'Autoscale On',
                color='#404040', hovercolor='#505050')
        self.autoscale.on_clicked(self._autoscale_click)
        self.autoscale.label.set_color('#eeeeee')

    def get_refresh_rate(self):
        return 1000 / self.refresh_ms

    def set_data_source(self, data_source_class, **kwargs):
        '''Set the source of data for the scope

           Must provide a subclass of ScopeDataSource which will be instantiated
           and called to provide the data.'''

        if not issubclass(data_source_class, ScopeDataSource):
            raise TypeError('data source must be a subclass of ScopeDataSource')

        self.datasource = data_source_class(self, **kwargs)
        self.fig.canvas.manager.set_window_title('PyScope [{}]'.format(data_source_class.__name__))

        self.datasource_thread = Thread(name='ScopeDataSource',
                target=self.datasource.produce_data)

    def start_data_source(self):
        '''Starts running the data source to provide samples.'''

        with self.lock:
            if self.datasource_running:
                return

            if not self.datasource_thread.is_alive():
                self.datasource_thread.start()

            self.datasource_running = True

    def stop_data_source(self):
        '''Inform the data source to stop after the next call to add_samples.'''

        with self.lock:
            self.datasource_running = False

        self.datasource_thread.join()


    def show(self, **kwargs):
        '''Show the scope plot.'''

        self._runstop_click()
        plt.show(**kwargs)

    def configure(self, samplerate, channels=1, channel_labels=None, ylabel=None, palate=None, fftref=1.0):
        '''Configure the data collection parameters.'''

        if palate is None:
            palate = self.even_hue_palate(channels, 60)
        self.samplerate = samplerate
        self.dt = 1 / samplerate
        self.channel_labels = channel_labels
        self.fftref = fftref

        # initialize plot data
        self.tdata = []
        self.ydata = []
        self.lines = []
        self.fdata = []
        self.mdata = []
        self.ffts = []
        self.sample_cache = []
        self.lock = Lock()

        for i in range(channels):
            self.ydata.append([])
            self.mdata.append([])
            self.sample_cache.append([])

            self.lines.append(Line2D(self.tdata, self.ydata[i], color=palate[i]))
            self.ffts.append(Line2D(self.fdata, self.mdata[i], color=palate[i]))

            self.axt.add_line(self.lines[i])
            if self.fft:
                self.axf.add_line(self.ffts[i])

        if ylabel is not None:
            self.axt.set_ylabel(ylabel)

        if channel_labels is not None:
            if self.fft:
                self.axf.legend(channel_labels)
            else:
                self.axt.legend(channel_labels)

    def save_data_csv(self, filename):
        '''Save the captured data series in CSV format.'''

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            if self.channel_labels != None:
                writer.writerow(['Time', *self.channel_labels])
            else:
                writer.writerow(['Time', *[ 'CH%d' % i for i in range(len(self.ydata)) ] ])

            for row in zip(self.tdata, *self.ydata):
                writer.writerow(row)

    def add_samples(self, samples):
        '''Add data samples from a data source. Thread safe.

           Samples may be a one dimensional array with one data sample per channel or
           a 2D array of such 1D samples. It may also be an empty array in which case
           this function call acts as a poll of the running flag.

           Returns True/False indicating if the data source should continue running.'''

        if not hasattr(samples, '__len__') or len(samples) == 0:
            return self.datasource_running

        # ensure 2D set of samples
        if not hasattr(samples[0], '__len__'):
            samples = [samples]

        with self.lock:
            for sample in samples:
                for i in range(len(self.ydata)):
                    self.sample_cache[i].append(sample[i])

            running = self.datasource_running

        return running

    def dbfft(self, x, fs=1, win=None, ref=32768):
        """
        Calculate spectrum in dB scale
        Args:
            x: input signal
            fs: sampling frequency
            win: vector containing window samples (same length as x).
                 If not provided, then rectangular window is used by default.
            ref: reference value used for dBFS scale. 32768 for int16 and 1 for float

        Returns:
            freq: frequency vector
            s_db: spectrum in dB scale
        """

        N = len(x)  # Length of input sequence

        if win is None:
            win = np.ones(N)
        elif callable(win):
            win = win(N)
        if len(x) != len(win):
                raise ValueError('Signal and window must be of the same length')
        x = x * win

        # Calculate real FFT and frequency vector
        sp = np.fft.rfft(x)
        freq = np.arange(((N + 1)/ 2)) / (float(N) / fs)

        # Scale the magnitude of FFT by window and factor of 2,
        # because we are using half of FFT spectrum.
        s_mag = np.abs(sp) * 2 / np.sum(win)

        # Convert to dBFS
        s_dbfs = 20 * np.log10(s_mag/ref)

        return freq, s_dbfs

    def _hsv2rgb(self, h, s, v):
        '''Convert HSV color to hex RGB string.'''
        return '#%02x%02x%02x' % tuple(round(i * 255) for i in hsv_to_rgb(h, s, v))

    def even_hue_palate(self, n_colors, phase):
        '''Generate a color palate with n colors evenly spaced in Hue starting at a specific phase.'''
        colors = []
        for i in range(round(phase), round(360+phase), round(360/n_colors)):
             colors.append(self._hsv2rgb(i/360, 1, 1))
        return colors

    def _on_resize(self, event):
        if len(self.tdata) > 0:
            self.fig.tight_layout(rect=(0, 0, 1, 0.9))
            self.fig.canvas.draw()

    def _emitter(self):
        '''Emits data from the thread safe intermediate sample cache to the animated plot.'''

        while True:
            with self.lock:
                plotdata = self.sample_cache
                self.sample_cache = [[] for i in range(len(self.ydata))]
            yield plotdata

    def _update(self, samples):
        '''Updates the animation for the current frame.'''

        # nothing to do unless there's more data
        numsamples = len(samples[0])
        if numsamples == 0:
            return

        # add the time values
        if len(self.tdata) == 0:
            now = 0
            # initialize the y limits with first set of data
            if self.autoscale_en:
                self.ymax = np.max(samples)
                self.ymin = np.min(samples)
                self._set_ylim()
        else:
            now = self.tdata[-1] + self.dt
        self.tdata.extend([now + i * self.dt for i in range(numsamples)])
        now = self.tdata[-1] - self.dt

        # update the y limits
        if self.autoscale_en:
            ymax = np.max(samples)
            if ymax > self.ymax:
                self.ymax = ymax
                self._set_ylim()

            ymin = np.min(samples)
            if ymin < self.ymin:
                self.ymin = ymin
                self._set_ylim()

        # add the data samples
        plot_samples = round(self.plot_widths[self.plot_width_idx] * self.samplerate) + 2
        if plot_samples < 128:
            plot_samples = 128
        for i in range(len(self.ydata)):
            self.ydata[i].extend(samples[i])

            visible_data = self.ydata[i][-plot_samples:-1]
            self.lines[i].set_data(self.tdata[-plot_samples:-1], visible_data)

            # TODO support options for window and fixed FFT size (pad data or slide fft and aggregate as needed)
            if self.fft:
                self.fdata, self.mdata[i] = self.dbfft(visible_data, fs=self.samplerate, ref=self.fftref,
                        win=np.hanning) #np.kaiser(len(visible_data), 14))
                self.ffts[i].set_data(self.fdata, self.mdata[i])

        self.axt.set_xlim(now - self.plot_widths[self.plot_width_idx], now)
        if self.fft:
            self.axf.set_xlim(self.fdata[0], self.fdata[-1])

        return self.lines + self.ffts

    def _runstop_click(self, event=None):
        if self.running:
            self.anim.event_source.stop()
            self.running = False
            self.runstop.label.set_text('Run')
            self.runstop.color = '#ff4040'
            self.runstop.hovercolor = '#ff7070'
            for i in range(len(self.ydata)):
                self.lines[i].set_data(self.tdata, self.ydata[i])
        else:
            if self.datasource_thread is None:
                return

            self.start_data_source()

            self.anim.event_source.start()
            self.running = True
            self.runstop.label.set_text('Stop')
            self.runstop.color = '#40ff40'
            self.runstop.hovercolor = '#70ff70'
        plt.draw()

    def _set_xlim(self):
        if self.running:
            now = self.tdata[-1]
            self.axt.set_xlim(now - self.plot_widths[self.plot_width_idx], now)
        else:
            left, right = self.axt.get_xlim()
            center = (left + right) / 2
            left = center - (self.plot_widths[self.plot_width_idx] / 2)
            right = center + (self.plot_widths[self.plot_width_idx] / 2)
            self.axt.set_xlim(left, right)
        plt.draw()

    def _width_next_click(self, event):
        if self.plot_width_idx < (len(self.plot_widths) - 1):
            self.plot_width_idx += 1
            self._set_xlim()

    def _width_prev_click(self, event):
        if self.plot_width_idx > 0:
            self.plot_width_idx -= 1
            self._set_xlim()

    def _set_ylim(self):
        ybuffer = (self.ymax - self.ymin) / 10 if (self.ymax - self.ymin) > 10 else 1
        self.axt.set_ylim(self.ymin - ybuffer, self.ymax + ybuffer)

    def _autoscale_click(self, event):
        self.autoscale_en = not self.autoscale_en
        if self.autoscale_en:
            self.autoscale.label.set_text('Autoscale On')
            self.ymax = np.max(self.ydata)
            self.ymin = np.min(self.ydata)
            self._set_ylim()
        else:
            self.autoscale.label.set_text('Autoscale Off')
        plt.draw()

