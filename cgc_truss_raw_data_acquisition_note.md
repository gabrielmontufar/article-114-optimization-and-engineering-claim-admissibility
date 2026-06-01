# Raw published truss published-response data acquisition

The truss published-response validation uses the public Zenodo dataset
`10.5281/zenodo.15658671`, "Latent resistance mechanisms of steel truss bridges
after critical failures - Experimental dataset". The dataset contains sensor
records from displacement transducers and strain gauges collected during
component-removal tests on a scaled steel truss bridge specimen.

The raw workbook is not bundled in the submission ZIP. Reviewers who want to
rerun the optional raw-data reconstruction should obtain it directly from the
public Zenodo record and preserve attribution under the Creative Commons
Attribution 4.0 International license. For optional raw reruns, place
`LatentMechanisms_SteelTruss_ExperimentalData.xlsx` in
`external_raw_datasets/Zenodo_15658671_SteelTruss/` or set the
`CGC_TRUSS_RAW_XLSX` environment variable to the workbook path.

The submission package includes compact processed response scores in
`cgc_truss_experimental_response.csv`, the raw-data manifest in
`cgc_truss_raw_data_manifest.csv`, the validation script, the validation details,
and the validation summary. The evidence supports published truss-family
response-state validation only. It is not safety certification, professional
approval, complete regulatory approval, or a physical test of the numerical
ten-bar benchmark itself.

Reuse note: cite Reyes et al., Zenodo record `10.5281/zenodo.15658671`, and
preserve attribution to the original creators under CC BY 4.0.



