# shoghicp-radio-dl
Python script for downloading tracks off of shoghicp's radio.

## Requirements
- Python >=3.7
- [requests](https://pypi.org/project/requests/)

## Usage
- Create an API key with miku on IRC and replace the `API_KEY` variable with your new key.
- Change other settings as you see fit (download location, download threads, filename template).
- Run the script with your desired search query. For example:
```
python shoghicp-radio-dl.py artist:aimer title:dare ga
```
