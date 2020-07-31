# BEKB OFX

Some banks have implemented statement download as an afterthought. The download cannot be fine-tuned with filters, contains the very minimum of fields and is therefore not very helpful for importing into personal finance Apps. The ones I am targeting require OFX imports.

This script is based on screenscraping (BeautifulSoup 4 with Selenium) and is customised to be used with the Berner Kantonalbank (BEKB) which only provides statement downloads in MT940 format. The MT940 file does not contain enough information for my needs. I wrote a separate script to parse MT940 into OFX <here, provide link>, which is not used here. 

The code does the following:

- Contacts the BEKB login page (evidently you need to provide your own account information and follow through 2-step authentication with the bank's mobile app)
- Once redirected to the statement page, it screenscrapes account and balance information, as well as the transactions as displayed (i.e. no filtering through Selenium for the moment)
- Parses the data to JSON file
- Parses the JSON file into OFX

I split the parsing into intermediate JSON file and then OFX file so that you can implement parsing to another format than OFX.

Use:

$ python ofx.py

Outputs are a JSON file and OFX file. The code has a hard-coded dict for translation of transaction types to Debit/Credit as needed for OFX. It is not a comprehensive list and could do with refactoring into an externally read lookup file.

Acknowledgments:
I had inspiration from other authors on topics about OFX:

<https://github.com/csingley/ofxtools>  
<https://gist.github.com/mdornseif/5676104>
