# REfind

<img src="refind-logo.png" alt="REfind logo" width="800"/>

# demo
REfind scrapes, parses, and transforms data from Redfin.com to generate comparative analysis reports, providing investment insights in both PDF and CSV/TSV formats.

![REfind Demo](https://github.com/isaiah-garcia/REfind/blob/main/refind-demo.gif)

# PDF reports 
REfind compares each comp to the subject to determine similarities and calculate the property value based on comp averages. Comps most similar to the subject property are colored green. 

REfind will color certain cells red if the comp was sold over 90 days ago, is missing important information, or the build date is 20 years apart from the subject.

<img src="REfind%20PDF%20sample.png" alt="REfind sample PDF" width="700"/>


# TSV reports

<img src="REfind%20tsv%20spreadsheet.png" alt="REfind sample spreadsheet" width="700"/>

## Installation

Selenium uses a driver (I recommend Chromedriver), so you will need to download a version of Chromedriver that is compatible with your device and with your current Google Chrome browser version ([download here](https://googlechromelabs.github.io/chrome-for-testing/#stable)). To check your Chrome browser version, you can find it in your settings here: [chrome://settings/help](chrome://settings/help)

```bash
pip install -r requirements.txt
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
