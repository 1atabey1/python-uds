#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


from uds.uds_config_tool import DecodeFunctions
import sys
from uds.uds_config_tool.FunctionCreation.iServiceMethodFactory import IServiceMethodFactory


# When encode the dataRecord for transmission we have to allow for multiple elements in the data record
# i.e. 'value1' - for a single value, or [('param1','value1'),('param2','value2')]  for more complex data records
requestFuncTemplate = str("def {0}(dataRecord):\n"
                          "    encoded = []\n"
                          "    if type(dataRecord) == list:\n"
                          "        drDict = dict(dataRecord)\n"
                          "        {3}\n"
                          "{4}\n"
                          "    return {1} + {2} + encoded")									 


checkFunctionTemplate = str("def {0}(input):\n"
                            "    serviceIdExpected = {1}\n"
                            "    diagnosticIdExpected = {2}\n"
                            "    serviceId = DecodeFunctions.buildIntFromList(input[{3}:{4}])\n"
                            "    diagnosticId = DecodeFunctions.buildIntFromList(input[{5}:{6}])\n"
                            "    if(len(input) != {7}): raise Exception(\"Total length returned not as expected. Expected: {7}; Got {{0}}\".format(len(input)))\n"
                            "    if(serviceId != serviceIdExpected): raise Exception(\"Service Id Received not expected. Expected {{0}}; Got {{1}} \".format(serviceIdExpected, serviceId))\n"
                            "    if(diagnosticId != diagnosticIdExpected): raise Exception(\"Diagnostic Id Received not as expected. Expected: {{0}}; Got {{1}}\".format(diagnosticIdExpected, diagnosticId))")

negativeResponseFuncTemplate = str("def {0}(input):\n"
                                   "    {1}")

encodePositiveResponseFuncTemplate = str("def {0}(input):\n"
                                         "    return")

class WriteDataByIdentifierMethodFactory(IServiceMethodFactory):

    ##
    # @brief method to create the request function for the service element
    @staticmethod
    def create_requestFunction(diagServiceElement, xmlElements):
        serviceId = 0
        diagnosticId = 0

        shortName = "request_{0}".format(diagServiceElement.find('SHORT-NAME').text)
        requestElement = xmlElements[diagServiceElement.find('REQUEST-REF').attrib['ID-REF']]
        paramsElement = requestElement.find('PARAMS')

        encodeFunctions = []
        encodeFunction = "None"
        debug_count = 0  # ??????????????????????temp count only

        for param in paramsElement:
            semantic = None
            try:
                semantic = param.attrib['SEMANTIC']
            except AttributeError:
                pass

            if(semantic == 'SERVICE-ID'):
                serviceId = [int(param.find('CODED-VALUE').text)]
            elif(semantic == 'ID'):
                diagnosticId = DecodeFunctions.intArrayToIntArray([int(param.find('CODED-VALUE').text)], 'int16', 'int8')
            elif semantic == 'DATA':
                dataObjectElement = xmlElements[(param.find('DOP-REF')).attrib['ID-REF']]
                longName = param.find('LONG-NAME').text
                bytePosition = int(param.find('BYTE-POSITION').text)
                """ ?????????????????????????????????????????????????????????????????????????????????
				This code is currently thrown by Structures, as there isno immediate 'DIAG-CODED-TYPE' e.g. in the form ...
            <STRUCTURE ID="_Bootloader_92">
              <SHORT-NAME>Module_Clock_Source</SHORT-NAME>
              <LONG-NAME>Module Clock Source</LONG-NAME>
              <BYTE-SIZE>1</BYTE-SIZE>
              <PARAMS>
                <PARAM SEMANTIC="DATA" xsi:type="VALUE">
                  <SHORT-NAME>Xtral</SHORT-NAME>
                  <LONG-NAME>Xtral</LONG-NAME>
                  <BYTE-POSITION>0</BYTE-POSITION>
                  <DOP-REF ID-REF="_Bootloader_21"/>
                </PARAM>
                <PARAM SEMANTIC="DATA" xsi:type="VALUE">
                  <SHORT-NAME>PLL</SHORT-NAME>
                  <LONG-NAME>PLL</LONG-NAME>
                  <BYTE-POSITION>0</BYTE-POSITION>
                  <BIT-POSITION>1</BIT-POSITION>
                  <DOP-REF ID-REF="_Bootloader_21"/>
                </PARAM>
                <PARAM xsi:type="RESERVED">
                  <SHORT-NAME>RESERVED_TO_FILL_STRUCTURE_0</SHORT-NAME>
                  <BYTE-POSITION>0</BYTE-POSITION>
                  <BIT-POSITION>2</BIT-POSITION>
                  <BIT-LENGTH>6</BIT-LENGTH>
                </PARAM>
              </PARAMS>
            </STRUCTURE>

                ... I need to discuss the handling of these with Richard - in the meantime, I'm ignoring this one!			
                """
                # Cathing any exceptions where we don't know the type - these will fail elsewhere, but at least we can test what does work.
                try:
                    encodingType = dataObjectElement.find('DIAG-CODED-TYPE').attrib['BASE-DATA-TYPE']
                except:
                    encodingType = "unknown"  # ... for now just drop into the "else" catch-all ??????????????????????????????????????????????
                if(encodingType) == "A_ASCIISTRING":
                    functionStringList = "DecodeFunctions.stringToIntList(dataRecord['{0}'], None)".format(longName)
                    functionStringSingle = "DecodeFunctions.stringToIntList(dataRecord, None)"
                elif(encodingType) == "A_INT8":
                    functionStringList = "DecodeFunctions.intArrayToIntArray(dataRecord['{0}'], 'int8', 'int8')".format(longName)
                    functionStringSingle = "DecodeFunctions.intArrayToIntArray(dataRecord, 'int8', 'int8')"
                elif(encodingType) == "A_INT16":
                    functionStringList = "DecodeFunctions.intArrayToIntArray(dataRecord['{0}'], 'int16', 'int8')".format(longName)
                    functionStringSingle = "DecodeFunctions.intArrayToIntArray(dataRecord, 'int16', 'int8')"
                elif(encodingType) == "A_INT32":
                    functionStringList = "DecodeFunctions.intArrayToIntArray(dataRecord['{0}'], 'int32', 'int8')".format(longName)
                    functionStringSingle = "DecodeFunctions.intArrayToIntArray(dataRecord, 'int32', 'int8')"
                else:
                    functionStringList = "dataRecord['{0}']".format(longName)
                    functionStringSingle = "dataRecord"

                """ No input types in intArrayToIntArray for anyhting else at present ... extend in DecodeFunction.py first ...
                elif(encodingType) == "A_INT64":
                    functionStringList = DecodeFunctions.intArrayToIntArray([int(param.find('CODED-VALUE').text)], 'int64', 'int8')
                """

                """
?????????????????????? need to cater for ...
BASE-DATA-TYPE="A_UINT32"
BASE-DATA-TYPE="A_BYTEFIELD"  ... these are already in the test ODX file

Any others?
    A_VOID: pseudo type for non-existing elements
    A_BIT: one bit
    A_UINT8: unsigned integer 8-bit
    A_UINT16: unsigned integer 16-bit
    A_UINT32: unsigned integer 32-bit
    A_INT8: signed integer 8-bit, two's complement
    A_INT16: signed integer 16-bit, two's complement
    A_INT32: signed integer 32-bit, two's complement
    A_INT64: signed integer 64-bit, two's complement
    A_FLOAT32: IEEE 754 single precision
    A_FLOAT64: IEEE 754 double precision
    A_ASCIISTRING: string, ISO-8859-1 encoded
    A_UTF8STRING: string, UTF-8 encoded
    A_UNICODE2STRING: string, UCS-2 encoded
    A_BYTEFIELD: Field of bytes
	
Anything on scaling?
????????????????? this is from the rdbi response formatting - we need to invert this to go the other way
                """

                # 
                encodeFunctions.append("encoded += [{1}]".format(longName,
                                                                 functionStringList))
                encodeFunction = "    else:\n        encoded = [{1}]".format(longName,functionStringSingle)



        # If we have only a single value for the dataRecord to send, then we can simply suppress the single value sending option.
        # Note: in the reverse case, we do not suppress the dictionary method of sending, as this allows extra flexibility, allowing 
        # a user to use a consistent list format in all situations if desired.
        if len(encodeFunctions) > 1:
            encodeFunction = ""

        funcString = requestFuncTemplate.format(shortName,
                                                serviceId,
                                                diagnosticId,
												"\n        ".join(encodeFunctions),  # ... handles input via list
												encodeFunction)                  # ... handles input via single value
        exec(funcString)
        return locals()[shortName]

    ##
    # @brief method to create the function to check the positive response for validity
    @staticmethod
    def create_checkPositiveResponseFunction(diagServiceElement, xmlElements):
        responseId = 0
        diagnosticId = 0

        shortName = diagServiceElement.find('SHORT-NAME').text
        checkFunctionName = "check_{0}".format(shortName)
        positiveResponseElement = xmlElements[(diagServiceElement.find('POS-RESPONSE-REFS')).find('POS-RESPONSE-REF').attrib['ID-REF']]

        paramsElement = positiveResponseElement.find('PARAMS')

        totalLength = 0

        for param in paramsElement:
            try:
                semantic = None
                try:
                    semantic = param.attrib['SEMANTIC']
                except AttributeError:
                    pass

                startByte = int(param.find('BYTE-POSITION').text)

                if(semantic == 'SERVICE-ID'):
                    responseId = int(param.find('CODED-VALUE').text)
                    bitLength = int((param.find('DIAG-CODED-TYPE')).find('BIT-LENGTH').text)
                    listLength = int(bitLength / 8)
                    responseIdStart = startByte
                    responseIdEnd = startByte + listLength
                    totalLength += listLength
                elif(semantic == 'ID'):
                    diagnosticId = int(param.find('CODED-VALUE').text)
                    bitLength = int((param.find('DIAG-CODED-TYPE')).find('BIT-LENGTH').text)
                    listLength = int(bitLength / 8)
                    diagnosticIdStart = startByte
                    diagnosticIdEnd = startByte + listLength
                    totalLength += listLength
                else:
                    pass
            except:
                print(sys.exc_info())
                pass

        checkFunctionString = checkFunctionTemplate.format(checkFunctionName, # 0
                                                           responseId, # 1
                                                           diagnosticId, # 2
                                                           responseIdStart, # 3
                                                           responseIdEnd, # 4
                                                           diagnosticIdStart, # 5
                                                           diagnosticIdEnd, # 6
                                                           totalLength) # 7

        # print(checkFunctionString)
        exec(checkFunctionString)
        return locals()[checkFunctionName]

    ##
    # @brief method to encode the positive response from the raw type to it physical representation
    @staticmethod
    def create_encodePositiveResponseFunction(diagServiceElement, xmlElements):
        # There's nothing to extract here! The only value in the response is the DID, checking of which is handled in the check function, 
        # so must be present and ok. This function is only required to return the default None response.
		
        shortName = diagServiceElement.find('SHORT-NAME').text
        encodePositiveResponseFunctionName = "encode_{0}".format(shortName)
		
        encodeFunctionString = encodePositiveResponseFuncTemplate.format(encodePositiveResponseFunctionName) # 0
        exec(encodeFunctionString)
        return locals()[encodePositiveResponseFunctionName]

    ##
    # @brief method to create the negative response function for the service element
    @staticmethod
    def create_checkNegativeResponseFunction(diagServiceElement, xmlElements):
        shortName = diagServiceElement.find('SHORT-NAME').text
        check_negativeResponseFunctionName = "check_negResponse_{0}".format(shortName)

        negativeResponsesElement = diagServiceElement.find('NEG-RESPONSE-REFS')

        negativeResponseChecks = []

        for negativeResponse in negativeResponsesElement:
            negativeResponseRef = xmlElements[negativeResponse.attrib['ID-REF']]

            negativeResponseParams = negativeResponseRef.find('PARAMS')

            for param in negativeResponseParams:

                semantic = None
                try:
                    semantic = param.attrib['SEMANTIC']
                except:
                    semantic = None

                if semantic == 'SERVICE-ID':
                    serviceId = param.find('CODED-VALUE').text
                    start = int(param.find('BYTE-POSITION').text)
                    diagCodedType = param.find('DIAG-CODED-TYPE')
                    bitLength = int((param.find('DIAG-CODED-TYPE')).find('BIT-LENGTH').text)
                    listLength = int(bitLength/8)
                    end = start + listLength

                    checkString = "if input[{0}:{1}] == {2}: raise Exception(\"Detected negative response: [hex(n) for n in input]\")".format(start,
                                                                                                                                              end,
                                                                                                                                              serviceId)
                    # print(checkString)
                    negativeResponseChecks.append(checkString)

                    pass
                pass

        negativeResponseFunctionString = negativeResponseFuncTemplate.format(check_negativeResponseFunctionName,
                                                                             "\n....".join(negativeResponseChecks))
        # print(negativeResponseFunctionString)
        exec(negativeResponseFunctionString)
        return locals()[check_negativeResponseFunctionName]