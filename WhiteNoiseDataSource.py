from time import sleep
import numpy as np
from Scope import ScopeDataSource

class WhiteNoiseDataSource(ScopeDataSource):
    '''Test scope data source providing a set of white noise outputs.'''

    def __init__(self, scope, samplerate=250, channels=1, **kwargs):
        self.scope = scope
        self.samplerate = samplerate
        self.channels = channels

        self.scope.configure(samplerate=samplerate, channels=channels)

    def produce_data(self):
        dt = 1 / self.samplerate
        running = True
        while running:
            numsamples = 10
            samples = []
            for i in range(numsamples):
                samples.append(np.random.normal(size=self.channels))

            running = self.scope.add_samples(samples)
            sleep(dt * numsamples)

