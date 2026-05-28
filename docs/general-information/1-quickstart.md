# Quick Start

Adding your own results for benchmarking is easy:

1. Pick a module that matches your experimental design from the [Benchmarking modules](../available-modules/index.rst)

2. Download the input data and supporting files from the module documentation (e.g. [DIA Astral LFQ](https://proteobench.readthedocs.io/en/stable/available-modules/active-modules/7-quant-lfq-ion-dia-Astral_2Th/#data-set]))

3. Run your analysis workflow on the downloaded input files 

4. Open the "Upload New Results" tab on the module page (e.g. for [DIA Astral LFQ](https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Astral)) on the WebApp and follow the instructions.

5. After uploading, the web app runs the ProteoBench scoring pipeline and shows
    interactive plots and tables comparing your run to public benchmarks.

We strongly recommend publishing your results to the public collection! Use the "Submit New Results" tab for that. All you have to add is the parameter file created by the workflow.

Tips and troubleshooting
--------------------------

- If your upload fails, check if you uploaded the correct output file(s), and if you used the correct input files with the original file names. If the problem still persists, please [let us know](https://github.com/Proteobench/ProteoBench/issues)! 
- Not sure which module is the best for you? Check out the [Benchmarking modules](../available-modules/index.rst). Your use case is not covered? [Let us know](../general-information/3-module-proposal)! 
- Make sure you have a stable internet connection. We rely on syncing results from GitHub, 
which can lead to connections errors, see [#259](https://github.com/Proteobench/ProteoBench/issues/259).

Need more help?
------------------

Feel free to reach out to us

1. via [GitHub](https://github.com/Proteobench/ProteoBench/issues) 
2. join our Slack channel on the [EuBIC](https://eubic-ms.org/onboarding/) slack 
3. contact us by email [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_troubleshooting)

You may also find a solution to your problem(s) here:
