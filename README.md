# `tqc-client`
A program for viewing QC statistics of `.fasta` and `.bam` files.

TQC is currently running on CLIMB, uploading new data every day. It has QC data going back to the `published_date` of `2022-03-02`. 

The `tqc-client` can retrieve data from TQC with the use of the `get` command, which will be detailed further below.

### Setup

#### 1. Clone this repository
```
$ git clone https://github.com/CLIMB-COVID/tqc-client.git
```

#### 2. Create and activate the conda environment
```
$ conda env create -f environment.yml
$ conda activate tqc-client 
```

#### 3. Set the required environment variables
The environment variables needed to use TQC are:

* `TQC_IP`: this is the hostname for TQC.
* `TQC_PORT`: this is the port number for TQC.

These can be provided by @tombch.

#### 4. Run the TQC client

We are now ready to use `tqc-client`. 

Data cannot be added to TQC by users. It can only be retrieved, using `get`, which will be detailed further below.

To run TQC and look at its options for retrieving data:

```
$ python tqc.py get --help
```

#### 5. [Optional] Bash function for ease of use
To run `tqc-client` from any directory, this function can be put into your `.bashrc` file with `<PATH-TO-DIR>` replaced by the directory for `tqc-client`.
```
function tqc() {
    python "<PATH-TO-TQC-DIR>/tqc.py" "$@"
}
export -f tqc
```

### Data stored in TQC

#### Metadata

* `central_sample_id`: this field is required in all TQC data.
* `run_name`: this field is required in all TQC data.
* `pag_name`: this field is required in all TQC data.
* `sequencing_org_code`
* `foel_producer`
* `phe_private_provider`
* `phe_site`
* `collection_date`
* `received_date`
* `sequencing_org_received_date`
* `sequencing_submission_date`
* `published_date`
* `fasta_path`: path to the `.fasta` file on CLIMB.
* `bam_path`: path to the `.bam` file on CLIMB.
* `library_primers`: formatted information on library primers.
* `library_primers_reported`: information on library primers, before formatting.
* `pag_suppressed`: whether the PAG has been suppressed or not. 
  * Each entry in this field is either `VALID` or `SUPPRESSED`.
  * **NOTE**: At the moment, TQC is **not** regularly reupdating its data.
  * This means that PAGs that have been recently suppressed may still be marked as 'VALID' in TQC.
  * I am working on implementing regular scans for changed metadata!
* `pag_basic_qc`: whether the PAG passed Majora basic QC.

#### Fasta QC

* `num_bases`: number of characters in the sequence.
* `pc_acgt`: the percentage of the characters `A`, `C`, `G` and `T` in the sequence.
* `pc_masked`: the percentage of the characters `N` and `X` in the sequence.
* `pc_ambiguous`: the percentage of the characters `W`, `S`, `M`, `K`, `R`, `Y`, `B`, `D`, `H` and `V` in the sequence.
* `pc_invalid`: the percentage of all other characters in the sequence that are not ACGT, masked or ambiguous.
* `longest_gap`: the length of the longest subsequence of masked and/or invalid bases in the sequence.
* `longest_ungap`: the length of the longest subsequence of ACGT and/or ambiguous bases in the sequence.

#### Bam QC
* `num_pos`: number of positions (the number of bases in the reference genome).
* `mean_cov`: mean coverage - this is the sum of coverages, divided by `num_pos`.
* `pc_pos_cov_gteX`: percentage of positions with coverage greater than or equal to `X`.
  * there are fields for `X = 1`, `X = 5`, `X = 10`, `X = 20`, `X = 50`, `X = 100`, and `X = 200`.

If `library_primers` information was given (that could be mapped to a `.bed` file):
* `pc_tiles_medcov_gteX`: the percentage of tiles with a median coverage greater than or equal to `X`.
  * there are fields for `X = 1`, `X = 5`, `X = 10`, `X = 20`, `X = 50`, `X = 100`, and `X = 200`.
* `tile_n`: the number of tiles.
* `tile_vector`: vector containing the median coverage for each tile.


#### Retrieving data from TQC

##### Overview 

Data is retrieved and written to `stdout` as a tab-separated table using the `get` command of TQC. 

##### Basic commands

The TQC database can be filtered by various arguments provided after `get`.

Passing multiple arguments to TQC will return only the rows that match **all** the constraints from the arguments.

For example, the command:

```
$ python tqc.py --published-date 2022-03-24 --library-primers 3
```

will return all rows that satisfy the following condition:

```
(published_date = 2022-03-22) AND (library_primers = 3)
```

Some arguments can be passed any number of values, and this will return rows that match **any** of the values within the argument.

For example, the command:

```
$ python tqc.py --published-date 2022-03-22 --library-primers 2 3 4
```

will return all rows that satisfy the following condition:

```
(published_date = 2022-03-22) AND ( (library_primers = 2) OR (library_primers = 3) OR (library_primers = 4) )
```

and the command:

```
$ python tqc.py --sequencing-org-code ABCD --published-date 2022-03-22 2022-03-24 --library-primers 2 3 4
```

will return all rows that satisfy the following condition:

```
(sequencing_org_code = ABCD) AND ( (published_date = 2022-03-22) OR (published_date = 2022-03-24) ) AND ( (library_primers = 2) OR (library_primers = 3) OR (library_primers = 4) )
```

#### Defaults

By default, TQC returns data only on **unsuppressed PAGs that passed basic QC**. The types of PAGs returned can be explicitly determined by passing `VALID` and/or `SUPPRESSED` to the `--pag-suppressed` argument, and passing `PASS` and/or `FAIL` to the `--pag-basic-qc` argument. 

To return all PAGs, add `--all` to the command. For example:

```
$ python tqc.py --all
```

will return *everything*.

#### Matching empty cells

String fields with empty cells can be matched by passing `_` to an argument, in place of a value.

For example, the command:

```
$ python tqc.py --published-date 2022-03-22 --library-primers 3 4 _
```

will return all rows that satisfy the following condition:

```
(published_date = 2022-03-22) AND ( (library_primers = 3) OR (library_primers = 4) OR (library_primers = EMPTY) )
```

where `EMPTY` denotes a cell in the `library_primers` column with the empty string as its value.

#### Numeric fields

Some fields store data as integers or floats, and these can be filtered using various operators. These operators are:

* `lt`: less than
* `gt`: greater than
* `leq`: less than or equal
* `geq`: greater than or equal
* `eq`: equal
* `neq`: not equal

To see which fields can be filtered using these operators, see `python tqc.py --help`.

For example, the command:

```
$ python tqc.py --published-date 2022-03-22 --pc-acgt leq 90 --pc-ambiguous gt 0
```

will return all rows that satisfy the following condition:

```
(published_date = 2022-03-22) AND (pc_acgt <= 90) AND (pc_ambiguous > 0)
```

The same numeric field can be passed more than once, unlike non-numeric fields.

For example, the command:

```
$ python tqc.py --pc-acgt geq 70 --pc-acgt leq 90 --pc-ambiguous gt 0
```

will return all rows that satisfy the following condition:

```
(70 <= pc_acgt <= 90) AND (pc_ambiguous > 0)
```

#### Date fields
There are five fields that store date information in TQC: `collection_date`, `received_date`, `sequencing_org_received_date`, `sequencing_submission_date` and `published_date`.

Rows can be matched by any number of individual dates:

```
$ python tqc.py --published-date 2022-03-02 2022-03-05 2022-03-06
```

this will return all rows that satisfy the following condition:

```
(published_date = 2022-03-02) OR (published_date = 2022-03-05) OR (published_date = 2022-03-06)
```

or between two dates:

```
$ python tqc.py --published-date-range 2022-03-02 2022-03-09
```

this will return all rows that satisfy the following condition:

```
 2022-03-02 <= published_date <= 2022-03-09
```

or by any number of individual ISO weeks (given in a `YYYY-WW` format):

```
$ python tqc.py --published-iso-week 2022-01 2022-04 2022-05
```

this will return all rows that satisfy the following condition:

```
(published_iso_week = 2022-01) OR (published_iso_week = 2022-04) OR (published_iso_week = 2022-05)
```

or between two ISO weeks:

```
$ python tqc.py --published-iso-week-range 2022-01 2022-05
```

this will return all rows that satisfy the following condition:

```
 2022-01 <= published_iso_week <= 2022-05
```

#### Additional metadata

The data returned by TQC can also be merged with additional metadata by giving the path to a `.tsv` file to the `--metadata` argument. This will display a **left join** between the TQC data and the given metadata table.

#### All arguments for `python tqc.py`

For reference.

```
$ python -m client.python tqc.py --help
usage: tqc.py get [-h] [--central-sample-id CENTRAL_SAMPLE_ID [CENTRAL_SAMPLE_ID ...]]
                  [--run-name RUN_NAME [RUN_NAME ...]] [--pag-name PAG_NAME [PAG_NAME ...]]
                  [--pag-suppressed PAG_SUPPRESSED [PAG_SUPPRESSED ...]]
                  [--pag-basic-qc PAG_BASIC_QC [PAG_BASIC_QC ...]] [--all]
                  [--sequencing-org-code SEQUENCING_ORG_CODE [SEQUENCING_ORG_CODE ...]]
                  [--foel-producer FOEL_PRODUCER [FOEL_PRODUCER ...]]
                  [--phe-private-provider PHE_PRIVATE_PROVIDER [PHE_PRIVATE_PROVIDER ...]]
                  [--phe-site PHE_SITE [PHE_SITE ...]] [--collection-pillar COLLECTION_PILLAR [COLLECTION_PILLAR ...]]
                  [--collection-date YYYY-MM-DD [YYYY-MM-DD ...] | --collection-date-range YYYY-MM-DD YYYY-MM-DD |
                  --collection-iso-week YYYY-WW [YYYY-WW ...] | --collection-iso-week-range YYYY-WW YYYY-WW]
                  [--received-date YYYY-MM-DD [YYYY-MM-DD ...] | --received-date-range YYYY-MM-DD YYYY-MM-DD |
                  --received-iso-week YYYY-WW [YYYY-WW ...] | --received-iso-week-range YYYY-WW YYYY-WW]
                  [--sequencing-org-received-date YYYY-MM-DD [YYYY-MM-DD ...] | --sequencing-org-received-date-range
                  YYYY-MM-DD YYYY-MM-DD | --sequencing-org-received-iso-week YYYY-WW [YYYY-WW ...] |
                  --sequencing-org-received-iso-week-range YYYY-WW YYYY-WW]
                  [--sequencing-submission-date YYYY-MM-DD [YYYY-MM-DD ...] | --sequencing-submission-date-range
                  YYYY-MM-DD YYYY-MM-DD | --sequencing-submission-iso-week YYYY-WW [YYYY-WW ...] |
                  --sequencing-submission-iso-week-range YYYY-WW YYYY-WW] [--published-date YYYY-MM-DD [YYYY-MM-DD ...]
                  | --published-date-range YYYY-MM-DD YYYY-MM-DD | --published-iso-week YYYY-WW [YYYY-WW ...] |
                  --published-iso-week-range YYYY-WW YYYY-WW] [--fasta-path FASTA_PATH [FASTA_PATH ...]]
                  [--bam-path BAM_PATH [BAM_PATH ...]] [--library-primers LIBRARY_PRIMERS [LIBRARY_PRIMERS ...]]
                  [--library-primers-reported LIBRARY_PRIMERS_REPORTED [LIBRARY_PRIMERS_REPORTED ...]]
                  [--num-bases OPERATOR VALUE] [--pc-acgt OPERATOR VALUE] [--pc-masked OPERATOR VALUE]
                  [--pc-invalid OPERATOR VALUE] [--pc-ambiguous OPERATOR VALUE] [--longest-gap OPERATOR VALUE]
                  [--longest-ungap OPERATOR VALUE] [--num-pos OPERATOR VALUE] [--mean-cov OPERATOR VALUE]
                  [--pc-pos-cov-gte1 OPERATOR VALUE] [--pc-pos-cov-gte5 OPERATOR VALUE]
                  [--pc-pos-cov-gte10 OPERATOR VALUE] [--pc-pos-cov-gte20 OPERATOR VALUE]
                  [--pc-pos-cov-gte50 OPERATOR VALUE] [--pc-pos-cov-gte100 OPERATOR VALUE]
                  [--pc-pos-cov-gte200 OPERATOR VALUE] [--pc-tiles-medcov-gte1 OPERATOR VALUE]
                  [--pc-tiles-medcov-gte5 OPERATOR VALUE] [--pc-tiles-medcov-gte10 OPERATOR VALUE]
                  [--pc-tiles-medcov-gte20 OPERATOR VALUE] [--pc-tiles-medcov-gte50 OPERATOR VALUE]
                  [--pc-tiles-medcov-gte100 OPERATOR VALUE] [--pc-tiles-medcov-gte200 OPERATOR VALUE]
                  [--tile-n OPERATOR VALUE] [--metadata TSV_PATH] [--host HOST] [--port PORT]

operators: lt, gt, leq, geq, eq, neq

options:
  -h, --help            show this help message and exit
  --central-sample-id CENTRAL_SAMPLE_ID [CENTRAL_SAMPLE_ID ...]
  --run-name RUN_NAME [RUN_NAME ...]
  --pag-name PAG_NAME [PAG_NAME ...]
  --pag-suppressed PAG_SUPPRESSED [PAG_SUPPRESSED ...]
                        Default: valid PAGs only
  --pag-basic-qc PAG_BASIC_QC [PAG_BASIC_QC ...]
                        Default: passed PAGs only
  --all                 Ignore defaults regarding PAG suppression and basic QC passing
  --sequencing-org-code SEQUENCING_ORG_CODE [SEQUENCING_ORG_CODE ...]
  --foel-producer FOEL_PRODUCER [FOEL_PRODUCER ...]
  --phe-private-provider PHE_PRIVATE_PROVIDER [PHE_PRIVATE_PROVIDER ...]
  --phe-site PHE_SITE [PHE_SITE ...]
  --collection-pillar COLLECTION_PILLAR [COLLECTION_PILLAR ...]
  --collection-date YYYY-MM-DD [YYYY-MM-DD ...]
  --collection-date-range YYYY-MM-DD YYYY-MM-DD
  --collection-iso-week YYYY-WW [YYYY-WW ...]
  --collection-iso-week-range YYYY-WW YYYY-WW
  --received-date YYYY-MM-DD [YYYY-MM-DD ...]
  --received-date-range YYYY-MM-DD YYYY-MM-DD
  --received-iso-week YYYY-WW [YYYY-WW ...]
  --received-iso-week-range YYYY-WW YYYY-WW
  --sequencing-org-received-date YYYY-MM-DD [YYYY-MM-DD ...]
  --sequencing-org-received-date-range YYYY-MM-DD YYYY-MM-DD
  --sequencing-org-received-iso-week YYYY-WW [YYYY-WW ...]
  --sequencing-org-received-iso-week-range YYYY-WW YYYY-WW
  --sequencing-submission-date YYYY-MM-DD [YYYY-MM-DD ...]
  --sequencing-submission-date-range YYYY-MM-DD YYYY-MM-DD
  --sequencing-submission-iso-week YYYY-WW [YYYY-WW ...]
  --sequencing-submission-iso-week-range YYYY-WW YYYY-WW
  --published-date YYYY-MM-DD [YYYY-MM-DD ...]
  --published-date-range YYYY-MM-DD YYYY-MM-DD
  --published-iso-week YYYY-WW [YYYY-WW ...]
  --published-iso-week-range YYYY-WW YYYY-WW
  --fasta-path FASTA_PATH [FASTA_PATH ...]
  --bam-path BAM_PATH [BAM_PATH ...]
  --library-primers LIBRARY_PRIMERS [LIBRARY_PRIMERS ...]
  --library-primers-reported LIBRARY_PRIMERS_REPORTED [LIBRARY_PRIMERS_REPORTED ...]
  --num-bases OPERATOR VALUE
  --pc-acgt OPERATOR VALUE
  --pc-masked OPERATOR VALUE
  --pc-invalid OPERATOR VALUE
  --pc-ambiguous OPERATOR VALUE
  --longest-gap OPERATOR VALUE
  --longest-ungap OPERATOR VALUE
  --num-pos OPERATOR VALUE
  --mean-cov OPERATOR VALUE
  --pc-pos-cov-gte1 OPERATOR VALUE
  --pc-pos-cov-gte5 OPERATOR VALUE
  --pc-pos-cov-gte10 OPERATOR VALUE
  --pc-pos-cov-gte20 OPERATOR VALUE
  --pc-pos-cov-gte50 OPERATOR VALUE
  --pc-pos-cov-gte100 OPERATOR VALUE
  --pc-pos-cov-gte200 OPERATOR VALUE
  --pc-tiles-medcov-gte1 OPERATOR VALUE
  --pc-tiles-medcov-gte5 OPERATOR VALUE
  --pc-tiles-medcov-gte10 OPERATOR VALUE
  --pc-tiles-medcov-gte20 OPERATOR VALUE
  --pc-tiles-medcov-gte50 OPERATOR VALUE
  --pc-tiles-medcov-gte100 OPERATOR VALUE
  --pc-tiles-medcov-gte200 OPERATOR VALUE
  --tile-n OPERATOR VALUE
  --metadata TSV_PATH
  --host HOST
  --port PORT
```
