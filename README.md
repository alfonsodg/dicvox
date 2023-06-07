# Dicvox

Image to **DICOM** converter

## Description

Dicvox is an application that allows you to convert jpg and png images into **DICOM**. It is especially useful when
certain
biomedical equipment does not offer **DICOM** export.
Additionally, it allows sending the converted image to the local **PACS** for dissemination among specialists.
The conversion process requires some mandatory minimum data such as **Modality**, **Media Storage Standard SOP Classes**
and
some patient data.

## DICOM References

Media Storage Standard SOP Classes:
https://dicom.nema.org/dicom/2013/output/chtml/part04/sect_i.4.html

Modalities:
http://dicomlookup.com/modalities.asp

## Getting Started

### Dependencies

* Languages: Python 3
* Multiple libraries such as **Pydicom**
* Linux, Windows, MacOS


### Installing

```shell
git clone https://github.com/alfonsodg/dicvox.git
pip install -r requirements.txt
```

### Testing **PACS**

The project includes a script that allows you to test the connection with the **PACS** using the dicom demo image included,
I recommend testing the case before configuring the application.

```shell
python test_send.py
```

### Executing program

```shell
python dicvox.py
```

### Configuration

The first time the application is started, a .db file is created that saves some basic configurations, these must be
modified during the first use of the application within the configuration window. The fields are self explanatory.
Restart the application when these values have been changed.

## Help

Please check the logs in the dicvox.log and the window shell before any request.

## Authors

Alfonso de la Guarda
[@alfonsodg](https://twitter.com/alfonsodg)

## Version History

* 1.0
    * Initial Release

## License

This project is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) License

## Acknowledgments

* [JPG to DICOM](https://github.com/jwitos/JPG-to-DICOM/blob/master/jpeg-to-dicom.py)
