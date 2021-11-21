# Sample Pollination Apps
A collection of sample apps for Pollination.

Pollination apps are built using [Streamlit app framework](https://github.com/streamlit/). 

If you are new Streamlit see their [get started documentation](https://docs.streamlit.io/library/get-started).

# NOTE

All the development for Pollination apps is in the alpha phase right now and we might
make major changes including some breaking changes. If you are developing an app for
a mission critical purpose make sure to pinpoint the version for the
`streamlit-pollination` dependency.

We currently do not support deploying the apps to Pollination. You can use a Pollination
API key to work with private resources. See [LEED Option II app](./leed-option-ii) as an
example.

Enjoy experimenting! :balloon: :balloon: :balloon:


# Sample apps

|  Name  |  Description |
| -- | -- |
| [Compare Daylight Results](./compare-daylight-results) | Helps compare daylight results between 2-3 runs in the same job. |
| [Daylight Factor App](./daylight-factor-app) | Creates a simple room and run daylight factor simulation on Pollination. |
| [Design Explorer](./design-explorer) | A prototype for building apps with parallel coordinates to do comparative studies. This app uses HiPlot. |
| [Energy Simulation Report](./energy-simulation-report) | An example of loading HTML outputs. |
| [Energy Use App](./energy-use) | An example for reading the results of an annual energy use sqlite file. |
| [EPW Visualization](./epw-viz) | An example for using Ladybug Python libraries. This app doesn't have dependencies on Pollination. |
| [LEED Option II](./leed-option-ii) | Visualize the outputs of the LEED Option II recipe in a report-like app. |


# Local development

1. Go to the subdirectory for each app.
2. Install app's dependencies.
3. Run the app.

Here is an example to run the **Design Explorer** app.

```
cd design_explorer
pip install -r requirements.txt
streamlit run app.py

```

# License
See each app's subfolder for app's license
