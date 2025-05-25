from time import sleep, perf_counter
from math import ceil
import numpy as np
from .scopedatasource import ScopeDataSource

class SinusoidDataSource(ScopeDataSource):
    '''Test scope data source providing a set of sinusoidal outputs.'''

    @classmethod
    def add_parser(cls, subparser):
        parser = subparser.add_parser('sin', description='Sin wave data source for testing')
        parser.add_argument('-s', '--samplerate', type=float, default=250, help='Samplerate in Hz')
        parser.add_argument('-f', '--frequency', type=float, default=0.5, help='Sinusoid frequency in Hz')
        parser.add_argument('-c', '--channels', type=int, default=8, help='Channel count')
        return parser

    def __init__(self, scope, samplerate=250, frequency=0.5, channels=8, **kwargs):
        self.scope = scope
        self.rate = samplerate
        self.freq = frequency
        self.channels = channels

        channel_labels = []
        self.phase = []
        for ch in range(self.channels):
            self.phase.append(ch* 2*np.pi/self.channels)
            channel_labels.append('cos(2*Pi*f*t + %d)' % round(self.phase[-1]*360/(2*np.pi)))

        self.scope.configure(samplerate=self.rate, channels=self.channels,
                channel_labels=channel_labels)

    def produce_data(self):
        i = 0
        f = self.freq
        dt = 1 / self.rate
        N = ceil(self.rate/50)
        if N < 10:
            N = 10
        running = True
        sleep_delta = 0
        alpha = 0.001
        behind = False
        while running:
            tic = perf_counter()
            samples = np.ndarray((N, self.channels))
            for n in range(N):
                t = i * dt
                for ch in range(self.channels):
                    samples[n][ch] = np.cos(2*np.pi*f*t + self.phase[ch])
                i += 1
            running = self.scope.add_samples(samples)
            toc = perf_counter()
            iter_t = toc - tic
            if iter_t >= (dt*N):
                if not behind:
                    print(f'ERROR: data source falling behind: {iter_t} >= {dt*N}')
                behind = True
            else:
                behind = False
                sleep_time = dt*N - iter_t - sleep_delta
                if sleep_time > 0:
                    tic = perf_counter()
                    sleep(sleep_time)
                    toc = perf_counter()
                    sleep_delta_now = (toc-tic) - sleep_time
                    sleep_delta = alpha*sleep_delta_now + (1-alpha)*sleep_delta

