from time import sleep
import numpy as np
from Scope import ScopeDataSource

class SinusoidDataSource(ScopeDataSource):
    '''Test scope data source providing a set of sinusoidal outputs.'''

    def __init__(self, scope, **kwargs):
        if 'samplerate' in kwargs:
            self.rate = kwargs['samplerate']
        else:
            self.rate = 250
        if 'frequency' in kwargs:
            self.freq = kwargs['frequency']
        else:
            self.freq = 0.5
        if 'channels' in kwargs:
            self.channels = kwargs['channels']
        else:
            self.channels = 8
        self.scope = scope

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
        running = True
        while running:
            samples = []
            for n in range(10):
                t = i * dt
                s = [np.cos(2*np.pi*f*t + self.phase[ch]) for ch in range(self.channels)]
                samples.append(s)
                i += 1
            running = self.scope.add_samples(samples)
            sleep(dt * 10)

