# Raw published published-response data acquisition

The raw published-response data used by `cgc_portal_frame_response_support.py`
come from the public DesignSafe/NEES project `NEES-2005-0101`, SAC Steel
Project Phase 2, Experiment 5. The downloaded files are the converted
`sac2rc01.txt` through `sac2rc10.txt` response curves.

The raw files are not bundled in the submission ZIP because they are third-party
public data and the redistribution license for this legacy NEES/DesignSafe
record was not confirmed as an open redistribution license. For optional raw
reruns, place `sac2rc01.txt` through `sac2rc10.txt` in
`external_raw_datasets/DesignSafe_NEES_2005_0101_Experiment5_SAC/` or set the
`CGC_PHYSICAL_RAW_DIR` environment variable to the folder containing those files.

To reproduce the acquisition, list and preview public DesignSafe files with:

```text
https://www.designsafe-ci.org/api/datafiles/agave/public/listing/nees.public/NEES-2005-0101.groups/Experiment-5/Trial-1/Rep-1/Converted_Data
https://www.designsafe-ci.org/api/datafiles/agave/public/preview/nees.public/NEES-2005-0101.groups/Experiment-5/Trial-1/Rep-1/Converted_Data/sac2rc01.txt/
```

The submission package includes processed service-envelope points in
`cgc_portal_frame_experimental_response.csv`, the raw-data manifest in
`cgc_portal_frame_raw_data_manifest.csv`, the validation script, and the
validation summary. The evidence supports published published-response agreement
for the tested steel moment-frame response family only. It is not a claim of
safety certification, AISC approval, professional certification, or complete
regulatory approval.




