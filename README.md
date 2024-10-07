# REfind
![REfind Logo](https://github.com/isaiah-garcia/REfind/blob/main/refind-logo.png)

# demo
REfind scrapes, parses, and transforms data from Redfin.com to generate comparative analysis reports, providing investment insights in both PDF and CSV/TSV formats.

![REfind Demo](https://github.com/isaiah-garcia/REfind/blob/main/refind-demo.gif?raw=true)

# PDF reports 
REfind compares each comp to the subject to determine similarities and calculate the property value based on comp averages. Comps most similar to the subject property are colored green. 

REfind will color certain cells red if the comp was sold over 90 days ago, is missing important information, or the build date is 20 years apart from the subject.

![REfind PDF example](https://github.com/isaiah-garcia/REfind/blob/main/REfind%20PDF%20sample.png)

# TSV reports
![REfind TSV example](https://github.com/isaiah-garcia/REfind/blob/main/REfind%20tsv%20spreadsheet.png)

## Installation

```bash
pip install -r requirements.txt
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
