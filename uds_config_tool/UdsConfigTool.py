#!/usr/bin/env python
import json
import xml.etree.ElementTree as ET

from uds_config_tool.FunctionCreation.ClearDTCMethodFactory import ClearDTCMethodFactory
from uds_config_tool.FunctionCreation.DiagnosticSessionControlMethodFactory import DiagnosticSessionControlMethodFactory
from uds_config_tool.FunctionCreation.ECUResetMethodFactory import ECUResetMethodFactory
from uds_config_tool.FunctionCreation.InputOutputControlMethodFactory import InputOutputControlMethodFactory
from uds_config_tool.FunctionCreation.ReadDTCMethodFactory import ReadDTCMethodFactory
from uds_config_tool.FunctionCreation.ReadDataByIdentifierMethodFactory import ReadDataByIdentifierMethodFactory
from uds_config_tool.FunctionCreation.RequestDownloadMethodFactory import RequestDownloadMethodFactory
from uds_config_tool.FunctionCreation.RequestUploadMethodFactory import RequestUploadMethodFactory
from uds_config_tool.FunctionCreation.RoutineControlMethodFactory import RoutineControlMethodFactory
from uds_config_tool.FunctionCreation.SecurityAccessMethodFactory import SecurityAccessMethodFactory
from uds_config_tool.FunctionCreation.TesterPresentMethodFactory import TesterPresentMethodFactory
from uds_config_tool.FunctionCreation.TransferDataMethodFactory import TransferDataMethodFactory
from uds_config_tool.FunctionCreation.TransferExitMethodFactory import TransferExitMethodFactory
from uds_config_tool.FunctionCreation.WriteDataByIdentifierMethodFactory import WriteDataByIdentifierMethodFactory
from uds_config_tool.ISOStandard.ISOStandard import IsoServices


def get_serviceIdFromXmlElement(diagServiceElement, xmlElements):
    requestKey = diagServiceElement.find('REQUEST-REF').attrib['ID-REF']
    requestElement = xmlElements[requestKey]
    params = requestElement.find('PARAMS')
    for i in params:
        try:
            if (i.attrib['SEMANTIC'] == 'SERVICE-ID'):
                return int(i.find('CODED-VALUE').text)
        except:
            pass

    return None


def fill_dictionary(xmlElement):
    temp_dictionary = {}
    for i in xmlElement:
        temp_dictionary[i.attrib['ID']] = i

    return temp_dictionary


def createUdsDefines(xmlFile):
    root = ET.parse(xmlFile)

    with open("odx-data.json", 'w') as outfile:
        json.dump({"Requests": [], "Responses": []}, outfile, indent=3)
        outfile.close()

    xmlElements = {}

    for child in root.iter():
        try:
            xmlElements[child.attrib['ID']] = child
        except KeyError:
            pass

    for key, value in xmlElements.items():
        if value.tag == 'DIAG-SERVICE':
            serviceId = get_serviceIdFromXmlElement(value, xmlElements)
            sdg = value.find('SDGS').find('SDG')
            humanName = ""
            for sd in sdg:
                try:
                    if sd.attrib['SI'] == 'DiagInstanceName':
                        humanName = sd.text
                except KeyError:
                    pass

            if serviceId == IsoServices.DiagnosticSessionControl:
                DiagnosticSessionControlMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.EcuReset:
                ECUResetMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.ReadDataByIdentifier:
                ReadDataByIdentifierMethodFactory.create_requestFunctions(value, xmlElements)

            elif serviceId == IsoServices.SecurityAccess:
                SecurityAccessMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.WriteDataByIdentifier:
                WriteDataByIdentifierMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.ClearDiagnosticInformation:
                ClearDTCMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.ReadDTCInformation:
                ReadDTCMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.InputOutputControlByIdentifier:
                InputOutputControlMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.RoutineControl:
                RoutineControlMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.RequestDownload:
                RequestDownloadMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.RequestUpload:
                RequestUploadMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.TransferData:
                TransferDataMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.RequestTransferExit:
                TransferExitMethodFactory.create_requestFunction(value, xmlElements)

            elif serviceId == IsoServices.TesterPresent:
                TesterPresentMethodFactory.create_requestFunction(value, xmlElements)
