# pyscope
Python oscilloscope-like data acquisition with easily pluggable data sources.

![SinusoidDataSource](https://github.com/mliss26/pyscope/blob/main/screenshots/pyscope_screenshot_sin.png "SinusoidDataSource Screenshot")
![WhiteNoiseDataSource](https://github.com/mliss26/pyscope/blob/main/screenshots/pyscope_screenshot_white.png "WhiteNoiseDataSource with FFT Screenshot")

# Dependencies
* [numpy](https://numpy.org)
* [matplotlib](https://matplotlib.org)

# Usage
```
usage: pyscope [-h] [--fft] {white,sin} ...

Python oscilloscope

positional arguments:
  {white,sin}

options:
  -h, --help   show this help message and exit
  --fft        show FFT below time domain plot
```
```
usage: pyscope white [-h] [-s SAMPLERATE] [-c CHANNELS]

White noise data source for testing

options:
  -h, --help            show this help message and exit
  -s, --samplerate SAMPLERATE
                        Samplerate in Hz
  -c, --channels CHANNELS
                        Channel count
```
```
usage: pyscope sin [-h] [-s SAMPLERATE] [-f FREQUENCY] [-c CHANNELS]

Sin wave data source for testing

options:
  -h, --help            show this help message and exit
  -s, --samplerate SAMPLERATE
                        Samplerate in Hz
  -f, --frequency FREQUENCY
                        Sinusoid frequency in Hz
  -c, --channels CHANNELS
                        Channel count
```

# DataSource API
Add a new data source by subclassing `ScopeDataSource` and calling `scope.add_samples(data_samples)`
in its `produce_data` method. See `SinusoidDataSource` and `WhiteNoiseDataSource` for example implementations.
