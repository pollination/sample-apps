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

You can get started by developing on top of these apps. Until we provide an official support for the apps as part of the Pollination platform, the live links that are provided will timeout when the app is inactive and you have to reload the page. The main purpose of providing these links is to make it easy for you to get a better sense of how these apps work.

|  Source code  |  Description | Live app |
| -- | -- | -- |
| [Compare Daylight Results](./compare-daylight-results/app.py) | Helps compare daylight results between 2-3 runs in the same job. | [Link](https://streamlit-experiment-compare-daylight-results-bctgvz4o3a-uc.a.run.app/) |
| [Daylight Factor App](./daylight-factor-app/app.py) | Creates a simple room and run daylight factor simulation on Pollination. | [Link](https://streamlit-experiment-daylight-factor-app-bctgvz4o3a-uc.a.run.app/) |
| [Design Explorer](./design-explorer/app.py) | A prototype for building apps with parallel coordinates to do comparative studies. This app uses HiPlot. | [Link](https://streamlit-experiment-design-explorer-bctgvz4o3a-uc.a.run.app/) |
| [Energy Simulation Report](./energy-simulation-report/app.py) | An example of loading HTML outputs. | [Link](https://streamlit-experiment-energy-simulation-report-bctgvz4o3a-uc.a.run.app/) |
| [Energy Use App](./energy-use/app.py) | An example for reading the results of an annual energy use sqlite file. | [Link](https://streamlit-experiment-energy-use-bctgvz4o3a-uc.a.run.app/) |
| [EPW Visualization](./epw-viz/app.py) | An example for using Ladybug Python libraries. This app doesn't have dependencies on Pollination. | [Link](https://streamlit-experiment-epw-viz-bctgvz4o3a-uc.a.run.app/) |
| [LEED Option II](./leed-option-ii/app.py) | Visualize the outputs of the LEED Option II recipe in a report-like app. | [Link](https://streamlit-experiment-leed-option-ii-bctgvz4o3a-uc.a.run.app/) |


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

# Deploying New Apps

To deploy new apps from this repository to Pollination's backend follow the instruction in [`pollination/sample-apps-devops`](https://github.com/pollination/sample-apps-devops).

# License
See each app's subfolder for app's license
