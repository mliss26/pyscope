# pyscope
Python oscilloscope-like data acquisition with easily pluggable data sources.

![SinusoidDataSource](https://github.com/mliss26/pyscope/blob/main/screenshots/pyscope_screenshot_sin.png "SinusoidDataSource Screenshot")
![WhiteNoiseDataSource](https://github.com/mliss26/pyscope/blob/main/screenshots/pyscope_screenshot_white.png "WhiteNoiseDataSource with FFT Screenshot")

# Dependencies
* [numpy](https://numpy.org)
* [matplotlib](https://matplotlib.org)

# Usage
```
usage: pyscope [-h] [-f] [-s {sin,white}]

Python oscilloscope

options:
  -h, --help            show this help message and exit
  -f, --fft             show FFT below time domain plot
  -s {sin,white}, --source {sin,white}
                        data source
```

# DataSource API
Add a new data source by subclassing `ScopeDataSource` and calling `scope.add_samples(data_samples)`
in its `produce_data` method. See `SinusoidDataSource` and `WhiteNoiseDataSource` for example implementations.
