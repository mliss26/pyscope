from time import sleep, perf_counter
from math import ceil
import numpy as np
from .scope import ScopeDataSource

class WhiteNoiseDataSource(ScopeDataSource):
    '''Test scope data source providing a set of white noise outputs.'''

    @classmethod
    def add_parser(cls, subparser):
        parser = subparser.add_parser('white', description='White noise data source for testing')
        parser.add_argument('-s', '--samplerate', type=float, default=500, help='Samplerate in Hz')
        parser.add_argument('-c', '--channels', type=int, default=2, help='Channel count')
        return parser

    def __init__(self, scope, samplerate=250, channels=1, **kwargs):
        self.scope = scope
        self.samplerate = samplerate
        self.channels = channels

        self.scope.configure(samplerate=samplerate, channels=channels)

    def produce_data(self):
        dt = 1 / self.samplerate
        N = ceil(self.samplerate/50)
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
                samples[n] = np.random.normal(size=self.channels)

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

